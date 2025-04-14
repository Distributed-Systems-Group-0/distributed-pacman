import os
import random
import time

from redis import Redis, WatchError

# REDIS_HOST = os.getenv("REDIS_HOST", "132.164.200.4")
# REDIS_PASS = os.getenv("REDIS_PASS", "qH2atSUTfW")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PASS = os.getenv("REDIS_PASS", None)

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

            parts = item.split(":")
            if len(parts) != 3:
                print(f"Skipping invalid movement key: {item}")
                pipe.unwatch()
                return  # or use 'continue' if iterating over multiple items

            _, entity, name = parts

            if score < current_time:
                # if entity == 'ghost':
                #     print("ghost here")
                pipe.multi()
                pipe.zrem("movements", item)
                pipe.hget(item, "n")
                pipe.hget(item, "d")
                pipe.hget(item, "x")
                pipe.hget(item, "y")
                response = pipe.execute()
                n, d, x, y = response[1:5]
                n, d, x, y = int(n), int(d), int(x), int(y)
                pipe.sismember("pellets", f"{x},{y}")
                p = pipe.execute()[0]
                
                if is_valid_move(n, x, y,entity):
                    if entity == 'ghost':
                        print("ghost here")
                    pipe.hset(item, "d", n)
                    new_x, new_y = calculate_new_position(n, x, y)
                    pipe.hset(item, "x", new_x)
                    pipe.hset(item, "y", new_y)
                    print(f"turned {item}")
                    if not p and entity == "player":
                        pipe.sadd("pellets", f"{x},{y}")
                        pipe.zincrby("leaderboard", 10, name)
                elif is_valid_move(d, x, y):
                    new_x, new_y = calculate_new_position(d, x, y)
                    pipe.hset(item, "x", new_x)
                    pipe.hset(item, "y", new_y)
                    print(f"moved {item}")
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
    # elif entity == 'ghost':
    #     if direction == 1:
    #         return maze[y % len(maze)][(x + 1) % len(maze[0])] == 3
    #     elif direction == 2:
    #         return maze[(y + 1) % len(maze)][x % len(maze[0])] == 3
    #     elif direction == 3:
    #         return maze[y % len(maze)][(x - 1) % len(maze[0])] == 3
    #     elif direction == 4:
    #         return maze[(y - 1) % len(maze)][x % len(maze[0])] == 3
    #     return False

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