import asyncio
import os
import random
import uuid

from asyncio import CancelledError
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from redis import WatchError
from redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PASS = os.getenv("REDIS_PASS", None)

redis_client = Redis(
    host=REDIS_HOST,
    password=REDIS_PASS,
    port=6379,
    db=0,
    decode_responses=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        send_task = asyncio.create_task(send_msgs())
        yield
    except CancelledError as e:
        pass
    finally:
        send_task.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/static",
    StaticFiles(directory="client"),
    name="static"
)

instance_uuid = str(uuid.uuid4())

clients: dict[str, WebSocket] = dict()

@app.get("/")
async def root():
    return FileResponse("client/index.html")

un_query = Query(
    ...,
    min_length=3,
    max_length=10,
    regex="^[0-9a-zA-Z]+$"
)

@app.websocket("/ws/pacman")
async def websocket_endpoint(
    ws: WebSocket,
    username: str = un_query
):
    key = f"conn:{username}"
    good = redis_client.set(key, "lock", nx=True, ex=1)
    if not good:
        print(f"{username} not good")
        await ws.close()
        return
    await ws.accept()
    clients[username] = ws
    if not register(username):
        print(f"{username} not register")
        await ws.close()
        return
    recv_task = asyncio.create_task(recv_msgs(ws, username))
    try:
        ping = {"type": "ping"}
        while True:
            await ws.send_json(ping)
            redis_client.expire(key, 1)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass
    except CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        recv_task.cancel()
        del clients[username]
        redis_client.delete(key)

def register(username: str):
    ct_s, ct_ms = redis_client.time()
    current_time = ct_s + ct_ms / 1_000_000
    with redis_client.pipeline() as pipe:
        try:
            pipe.watch(f"item:player:{username}")
            if not pipe.exists(f"item:player:{username}"):
                (x, y) = random_location()
                pacman = {
                    "username": username,
                    "x": x, "y": y,
                    "smoothX": x, "smoothY": y,
                    "f": 0, "n": 0, "d": 0
                }
                pipe.multi()
                pipe.hset(f"item:player:{username}", mapping=pacman)
                pipe.zadd("movements", {f"item:player:{username}": current_time})
                pipe.zadd("leaderboard", {f"{username}": 0})
                pipe.execute()
                print("hash created")
            else: print("hash already exists")
            return True
        except WatchError:
            print("race condition detected")
            return False

async def send_msgs():
    while True:
        try:
            while True:
                pipe = redis_client.pipeline()
                keys = list(redis_client.scan_iter("item:*"))
                for key in keys:
                    pipe.hgetall(key)
                result = pipe.execute()
                objects = {key: item for key, item in zip(keys, result)}
                for client in clients:
                    pipe.hget(f"item:player:{client}", "x")
                    x = int(pipe.execute()[0])
                    pipe.zrange("leaderboard", 0, -1, True, True)
                    lb = pipe.execute()[0]
                    try:
                        await clients[client].send_json({
                            "type": "state",
                            "content": {
                                "serverUUID": instance_uuid,
                                "pellets": pellets_spaces(x),
                                "objects": objects,
                                "leaderboard": lb
                            }
                        })
                    except Exception:
                        pass
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"hello world {e}")

async def recv_msgs(ws: WebSocket, username: str):
    try:
        while True:
            data = await ws.receive_text()
            key = f"item:player:{username}"
            redis_client.hset(key, "n", data)
    except CancelledError:
        return
    except WebSocketDisconnect:
        return

def pellets_spaces(x: int):
    coords = redis_client.smembers('pellets')
    empty_spaces = {
        (int(coord.split(',')[0]), int(coord.split(',')[1]))
        for coord in coords}
    open_spaces = {
        (i, j)
        for i in range(x-len(maze[0]),x+len(maze[0]))
        for j in range(len(maze))
        if maze[j % len(maze)][i % len(maze[0])] == 0}
    return list(open_spaces - empty_spaces)

def random_location():
    open_spaces = [
        (i,j)
        for i in range(len(maze[0]))
        for j in range(len(maze))
        if maze[j][i] == 0 ]
    return random.choice(open_spaces)

maze = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 2, 2, 1, 0, 1, 2, 2, 2, 1, 0, 1, 1, 0, 1, 2, 2, 2, 1, 0, 1, 2, 2, 1, 0, 1],
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