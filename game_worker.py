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
    with redis_client.pipeline() as pipe:
        try:
            pipe.watch("movements")
            items = pipe.zrange("movements", 0, 0, withscores=True)
            if len(items) == 0:
                return
            item, score = items[0]
            if redis_client.hlen(item) == 0:
                pipe.zrem('movements',item)
                pipe.execute()
                return
            parts = item.split(":")
            if len(parts) != 3:
                print(f"Skipping invalid movement key: {item}")
                pipe.unwatch()
                return  # or use 'continue' if iterating over multiple items

            _, entity, name = parts
            
            if score < current_time:
                pipe.multi()
                pipe.zrem("movements", item)
                pipe.hget(item, "n")
                pipe.hget(item, "d")
                pipe.hget(item, "x")
                pipe.hget(item, "y")
                response = pipe.execute()
                n, d, x, y = response[1:5]
                n, d, x, y = int(n), int(d), int(x), int(y)
                curr_player_maze = math.floor(int(x) / len(maze[0]))
                pipe.sismember("pellets", f"{x},{y}")
                p = pipe.execute()[0]
                
                if entity=='player':
                    collisions = set()
                    new_px, new_py = calculate_new_position(d,x,y)
                    for key in redis_client.scan_iter("item:ghost:*"):
                        pipe.hmget(key, ['x','y'])
                        list_XY = pipe.execute()[0]
                        
                        if f"{list_XY[0]},{list_XY[1]}" == f"{x},{y}":
                            collisions.add(key)
                            # print(f"Collision1: {collisions}")
                        elif f"{list_XY[0]},{list_XY[1]}" == f"{new_px},{new_py}":
                            collisions.add(key)
                            # print(f"Collision2: {collisions}")
                    if int(redis_client.hget(item, "status")) >0:
                        pipe.zincrby('leaderboard', len(collisions)*100, name)

                    elif len(collisions)>0:
                        pipe.hincrby(item, 'lives', -1)
                    for collision in collisions:
                        pipe.delete(collision)
                    pipe.execute()

                    lives = int(redis_client.hget(item, "lives"))
                    print(f"lives remaining: {lives}")
                    if  lives <= 0:
                        pipe.delete(item)
                        pipe.execute()
                        return
                
                if entity == "player":
                    print(f"curr player maze: {curr_player_maze}")
                    mazes = []
                    for key in redis_client.scan_iter("item:ghost:*"):
                        pipe.hmget(key, ['x', 'username'])
                        list_X = pipe.execute()[0][0]
                        # print(f"list_X: {list_X}")
                        curr_maze = math.floor(int(list_X) / len(maze[0]))
                        # print(f"curent maze: {curr_maze}")
                        mazes.append(curr_maze)
                    if curr_player_maze not in mazes:
                        # print("need to spawn ghost")
                        spawn_ghosts(curr_player_maze)
                
                if entity == 'player':
                    value = redis_client.hget(item, 'status')
                    if int(value) >= 1:
                        redis_client.hincrby(item, 'status', -1)

                if is_valid_move(n, x, y,entity):
                    # if entity == 'ghost':
                    #     print("ghost here")
                    pipe.hset(item, "d", n)
                    new_x, new_y = calculate_new_position(n, x, y)
                    pipe.hset(item, "x", new_x)
                    pipe.hset(item, "y", new_y)
                    # print(f"turned {item}")
                    if not p and entity == "player":
                        if (x,y) in power_pellets:
                            print(f"power pellet eaten")
                            pipe.hset(item, "status", 25)
                        else:
                            pipe.zincrby("leaderboard", 10, name)
                        pipe.sadd("pellets", f"{x},{y}")
                    
                elif is_valid_move(d, x, y):
                    new_x, new_y = calculate_new_position(d, x, y)
                    pipe.hset(item, "x", new_x)
                    pipe.hset(item, "y", new_y)
                    # print(f"moved {item}")
                    if not p and entity == "player":
                        pipe.sadd("pellets", f"{x},{y}")
                        pipe.zincrby("leaderboard", 10, name)
                elif entity == 'ghost':
                    new_n_choices = get_valid_directions(x,y)
                    new_n = random.choice(new_n_choices)
                    pipe.hset(item, "n", new_n)
                    pipe.hset(item, "d", new_n)
                    # print(f"new n choice {new_n_choices}")
                score = current_time + 0.2
                pipe.zadd("movements", {item: score})
                pipe.execute()
        except WatchError as e:
            # print(e.with_traceback())
            print("movements race condition detected")

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


def get_valid_directions(x, y):
    """Get list of valid directions from current position"""
    valid = []
    for direction in range(1, 5):
        if is_valid_move(direction, x, y):
            valid.append(direction)
    return valid
     
def is_valid_move(direction, x, y, entity = 'player'):
    if entity == 'player':
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