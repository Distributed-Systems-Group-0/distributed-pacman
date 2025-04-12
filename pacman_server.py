import asyncio
import datetime
import os
import random
import uuid

import fastapi
import redis

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect, Query

from datetime import datetime
from datetime import timedelta

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.Redis(
    host=REDIS_HOST,
    password=REDIS_PASSWORD,
    port=6379,
    db=0,
    decode_responses=True
)

app = fastapi.FastAPI()
app.mount("/static", StaticFiles(directory="client"), name="static")

instance_uuid = str(uuid.uuid4())

clients: dict[str, WebSocket] = dict()

@app.get("/")
async def root():
    return FileResponse("client/index.html")

@app.websocket("/ws/pacman")
async def websocket_endpoint(
    ws: WebSocket,
    username: str = Query(..., min_length=3, max_length=10, regex="^[0-9a-zA-Z]+$")
):
    vacant = redis_client.set(f"conn:{username}", "locked", nx=True, ex=1)

    if vacant:
        await ws.accept()
        clients[username] = ws
    else:
        return

    try:
        register(username)
        while True:
            redis_client.expire(f"conn:{username}", 1)
            data = await ws.receive_text()
            controls = {
                "ArrowRight": 1,
                "ArrowDown" : 2,
                "ArrowLeft": 3,
                "ArrowUp": 4
            }
            redis_client.hset(f"item:{username}", "n", controls[data])
            print(f"{username} input {controls[data]}")

    except WebSocketDisconnect:
        print(f"{username} disconnected")

    finally:
        clients.pop(username, None)
        redis_client.delete(f"conn:{username}")

def register(username):
    ct_s, ct_ms = redis_client.time()
    current_time = ct_s + ct_ms / 1_000_000
    with redis_client.pipeline() as pipe:
        try:
            pipe.watch(f"item:{username}")
            if not pipe.exists(f"item:{username}"):
                (x, y) = random_location()
                pacman = {
                    "username": username,
                    "x": x, "y": y,
                    "smoothX": x, "smoothY": y,
                    "f": 0, "n": 0, "d": 0
                }
                pipe.multi()
                pipe.hset(f"item:{username}", mapping=pacman)
                pipe.zadd("movements", {f"item:{username}": current_time})
                pipe.zadd("updates", {f"item:{username}": current_time})
                pipe.execute()
                print("hash created")
            else:
                print("hash already exists")
        except redis.WatchError:
            print("race condition detected")

def random_location():
    open_spaces = [
        (i,j)
        for i in range(len(maze[0]))
        for j in range(len(maze))
        if maze[j][i] == 0 ]
    return random.choice(open_spaces)

async def send_messages():
    try:
        while True:
            with redis_client.pipeline() as pipe:
                try:
                    pipe.watch("item:*")
                    while True:
                        pass
                except redis.WatchError:
                    for key in redis_client.scan_iter("item:*"):
                        pipe.hgetall(key)
                    content = pipe.execute()
            message = {
                "type": "gamestate",
                "sender": instance_uuid,
                "content": content
            }
            for client in clients:
                await clients[client].send_json(message)
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        print("send_messages task cancelled")
    except WebSocketDisconnect:
        print("send_messages task websocket disconnect")

app.add_event_handler(
    "startup",
    lambda: asyncio.create_task(send_messages())
)

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