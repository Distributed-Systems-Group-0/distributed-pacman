import math
import os
import random
import time
import uuid

from redis import Redis, WatchError

# REDIS_HOST = os.getenv("REDIS_HOST", "132.164.200.4")
# REDIS_PASS = os.getenv("REDIS_PASS", "qH2atSUTfW")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PASS = os.getenv("REDIS_PASS", None)
power_pellets = [(1,1), (26,1), (1,29), (26,29)]

redis_client = Redis(
    host=REDIS_HOST,
    password=REDIS_PASS,
    port=6379,
    db=0,
    decode_responses=True
)

def movements():
    ct_s, ct_ms = redis_client.time()
    current_time = ct_s + ct_ms / 1_000_000
    
    lua_script = """
    local items = redis.call('zrange', KEYS[1], 0, 0, 'WITHSCORES')
    if #items == 0 then
        return nil
    end
    redis.call('zrem', KEYS[1], items[1])
    return items
    """

    result = redis_client.eval(lua_script, 1, "movements")
    if result:
        item, score = result[0], float(result[1])
    else: return

    if redis_client.hlen(item) == 0:
        return
    
    parts = item.split(":")
    if len(parts) != 3:
        return
    
    _, entity, name = parts

    # now we can do whatever we want with the event

    if score < current_time:
        # lets carry out the event
        # print(item, score)

        n = redis_client.hget(item, "n")
        d = redis_client.hget(item, "d")
        x = redis_client.hget(item, "x")
        y = redis_client.hget(item, "y")
        n, d, x, y = int(n), int(d), int(x), int(y)
        curr_player_maze = math.floor(int(x) / len(maze[0]))
        p = redis_client.sismember("pellets", f"{x},{y}")

        if entity == "player":
            collisions = set()
            new_px, new_py = calculate_new_position(d, x, y)
            for key in redis_client.scan_iter("item:ghost:*"):
                xy = redis_client.hmget(key, ["x", "y"])
                if f"{xy[0]},{xy[1]}" == f"{x},{y}":
                    collisions.add(key)
                elif f"{xy[0]},{xy[1]}" == f"{new_px},{new_py}":
                    collisions.add(key)
            if int(redis_client.hget(item, "status")) > 0:
                redis_client.zincrby("leaderboard", len(collisions)*100, name)
            elif len(collisions) > 0:
                redis_client.hincrby(item, "lives", -1)
            for collision in collisions:
                redis_client.delete(collision)
            
            lives = int(redis_client.hget(item, "lives"))
            if lives <= 0:
                redis_client.delete(item)
                return
            
            player_movement_count = redis_client.incrby("dropper", 1)
            dropper_locations = []
            if player_movement_count > 50:
                for key in redis_client.scan_iter("item:dropper:*"):
                    tx = redis_client.hmget(key, ["x"])[0]
                    curr_dropper = math.floor(int(tx) / len(maze[0]))
                    dropper_locations.append(curr_dropper)
                if dropper_locations.count(curr_player_maze) < 5:
                    redis_client.set("dropper", 0)
                    spawn_dropper()

        if entity == "player":
            mazes = []
            for key in redis_client.scan_iter("item:ghost:*"):
                tx = redis_client.hmget(key, ["x"])[0]
                curr_maze = math.floor(int(tx) / len(maze[0]))
                mazes.append(curr_maze)
            if curr_player_maze not in mazes:
                spawn_ghosts(curr_player_maze)

        if entity == "player":
            value = redis_client.hget(item, "status")
            if int(value) >= 1:
                redis_client.hincrby(item, "status", -1)
        
        if is_valid_move(n, x, y):
            redis_client.hset(item, "d", n)
            new_x, new_y = calculate_new_position(n, x, y)
            redis_client.hset(item, "x", new_x)
            redis_client.hset(item, "y", new_y)
            if not p and entity == "player":
                if (x,y) in power_pellets:
                    redis_client.hset(item, "status", 25)
                else:
                    redis_client.zincrby("leaderboard", 10, name)
                redis_client.sadd("pellets", f"{x},{y}")
            if p and entity == "dropper":
                redis_client.srem("pellets", f"{x},{y}")
        elif is_valid_move(d, x, y):
            new_x, new_y = calculate_new_position(d, x, y)
            redis_client.hset(item, "x", new_x)
            redis_client.hset(item, "y", new_y)
            if not p and entity == "player":
                if (x,y) in power_pellets:
                    redis_client.hset(item, "status", 25)
                else:
                    redis_client.zincrby("leaderboard", 10, name)
                redis_client.sadd("pellets", f"{x},{y}")
            if p and entity == "dropper":
                redis_client.srem("pellets", f"{x},{y}")
        elif entity == "ghost" or entity == "dropper":
            new_n_choices = get_valid_directions(x,y)
            new_n = random.choice(new_n_choices)
            redis_client.hset(item, "n", new_n)

        # we will reschedule for a bit later
        # (since event was carried out)
        score = current_time + 0.25

    # lets reschedule the event

    redis_client.zadd("movements", {item: score})

def spawn_ghosts(mazeID, num_ghosts=4):
    ghost_colors = ["red", "pink", "cyan", "orange"]
    
    with redis_client.pipeline() as pipe:
            
        ct_s, ct_ms = redis_client.time()
        current_time = ct_s + ct_ms / 1_000_000        
        for i in range(num_ghosts):
            ghost_uuid = str(uuid.uuid4())
            ghost_color = ghost_colors[i % len(ghost_colors)]            
            x,y = 13+mazeID*len(maze[0]), 11
            random_direction = random.choice([1,3])
            ghost = {
                "username": ghost_uuid,
                "x": x, "y": y,
                "smoothX": x, "smoothY": y,
                "f": 0, "n": random_direction, "d": random_direction,
                "color": ghost_color,
                "mazeId": 0,  # Current maze ID (for infinite mazes)
            }
            pipe.hset(f"item:ghost:{ghost_uuid}", mapping=ghost)
            pipe.zadd("movements", {f"item:ghost:{ghost_uuid}": current_time})
        
        pipe.execute()
        # print(f"Created {num_ghosts} ghosts") 

def spawn_dropper(num_dropper=1):
    dropper_colors = ["brown"]
    try:
        with redis_client.pipeline() as pipe:
                
            ct_s, ct_ms = redis_client.time()
            current_time = ct_s + ct_ms / 1_000_000        
            for i in range(num_dropper):
                dropper_uuid = str(uuid.uuid4())
                dropper_color = dropper_colors[i % len(dropper_colors)]            
                # coords = redis_client.srandmember('pellets')
                (x,y) = tuple(redis_client.srandmember('pellets').split(','))
                random_direction = random.choice([1,2,3,4])
                dropper = {
                    "username": dropper_uuid,
                    "x": x, "y": y,
                    "smoothX": x, "smoothY": y,
                    "f": 0, "n": random_direction, "d": random_direction,
                    "color": dropper_color,
                    "mazeId": 0,  # Current maze ID (for infinite mazes)
                }
                pipe.hset(f"item:dropper:{dropper_uuid}", mapping=dropper)
                pipe.zadd("movements", {f"item:dropper:{dropper_uuid}": current_time})
            
            pipe.execute()
            # print(f"Created {num_ghosts} ghosts") 
    except WatchError:
        print("race condition problem for droppers")


def get_valid_directions(x, y):
    """Get list of valid directions from current position"""
    valid = []
    for direction in range(1, 5):
        if is_valid_move(direction, x, y):
            valid.append(direction)
    return valid
     
def is_valid_move(direction, x, y):
    if direction == 1:
        return maze[y % len(maze)][(x + 1) % len(maze[0])] == 0
    elif direction == 2:
        return maze[(y + 1) % len(maze)][x % len(maze[0])] == 0
    elif direction == 3:
        return maze[y % len(maze)][(x - 1) % len(maze[0])] == 0
    elif direction == 4:
        return maze[(y - 1) % len(maze)][x % len(maze[0])] == 0
    return False

def calculate_new_position(direction, x, y):
    if direction == 1:
        return x + 1, y
    elif direction == 2:
        return x, y + 1
    elif direction == 3:
        return x - 1, y
    elif direction == 4:
        return x, y - 1
    return x, y

maze = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 2, 2, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 2, 2, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 1, 0, 1, 1, 0, 1, 1, 1, 3, 3, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2, 2, 2, 2],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 3, 3, 3, 3, 3, 3, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 3, 3, 3, 3, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 3, 3, 3, 3, 3, 3, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2, 2, 2, 2],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1],
    [1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

while True:
    try:
        movements()
        # ghost_movements()
        time.sleep(0.01)
    except KeyboardInterrupt:
        print("program interrupted")
        break