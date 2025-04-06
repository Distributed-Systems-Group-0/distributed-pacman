
import asyncio
from datetime import datetime
from datetime import timedelta
import random
import time
import uuid
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import redis
import json
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
redis_host = os.getenv("REDIS_HOST","127.0.0.1")
redis_password = os.getenv("REDIS_PASSWORD")
redis_client = redis.Redis(host=redis_host, password=redis_password, port=6379, db=0, decode_responses=True)

instance_id = str(uuid.uuid4())

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="client"), name="static")

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
async def ws_endpoint(websocket: WebSocket, username: str = un_query):
    if 3 <= len(username) <= 10 and username.isalnum():
        if redis_client.set(f"conn:{username}", "locked", nx=True, ex=2):
            await websocket.accept()
            if redis_client.hsetnx(f"item:{username}", "username", username):
                (x, y) = random_location()
                redis_client.hset(f"item:{username}", "x", x)
                redis_client.hset(f"item:{username}", "y", y)
                redis_client.hset(f"item:{username}", "f", 0) # animated frame
                redis_client.hset(f"item:{username}", "n", 0) # next direction
                redis_client.hset(f"item:{username}", "d", 0) # direction
                redis_client.hset(f"item:{username}", "smoothX", x)
                redis_client.hset(f"item:{username}", "smoothY", y)
                current_time = datetime.now()
                future_time = current_time + timedelta(seconds=0.01)
                timestamp = str(future_time.timestamp())
                redis_client.zadd("smoothupdates", {username: timestamp})
                future_time = current_time + timedelta(seconds=2)
                timestamp = str(future_time.timestamp())
                redis_client.zadd("movements", {username: timestamp})
            asyncio.create_task(send_updates(websocket, username))
            await handle_messages(websocket, username)
        else:
            raise HTTPException(status_code=403, detail="Username already taken.")
    else:
        raise HTTPException(status_code=403, detail="Username not suitable.")

async def manage_movements():
    while True:
        if redis_client.set(f"lock:movements", "locked", nx=True, ex=1):
            print("lock obtained for movements")
            items = redis_client.zrange('movements', 0, 0, withscores=True)
            if len(items) > 0:
                (username, score) = items[0]
                current_time = datetime.now().timestamp()
                if current_time > float(score):
                    redis_client.zrem("movements", username)
                    dir = redis_client.hget(f"item:{username}", "n")
                    x = int(redis_client.hget(f"item:{username}", "x"))
                    y = int(redis_client.hget(f"item:{username}", "y"))
                    if int(dir) == 1 and maze[y % len(maze)][(x + 1) % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "d", dir)
                    elif int(dir) == 2 and maze[(y + 1) % len(maze)][x % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "d", dir)
                    elif int(dir) == 3 and maze[y % len(maze)][(x - 1) % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "d", dir)
                    elif int(dir) == 4 and maze[(y - 1) % len(maze)][x % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "d", dir)
                    dir = redis_client.hget(f"item:{username}", "d")
                    if int(dir) == 1 and maze[y % len(maze)][(x + 1) % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "x", x + 1)
                    elif int(dir) == 2 and maze[(y + 1) % len(maze)][x % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "y", y + 1)
                    elif int(dir) == 3 and maze[y % len(maze)][(x - 1) % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "x", x - 1)
                    elif int(dir) == 4 and maze[(y - 1) % len(maze)][x % len(maze[0])] == 0:
                        redis_client.hset(f"item:{username}", "y", y - 1)
                    current_time = datetime.now()
                    future_time = current_time + timedelta(seconds=0.2)
                    timestamp = str(future_time.timestamp())
                    redis_client.zadd("movements", {username: timestamp})
            redis_client.delete(f"lock:movements")
        await asyncio.sleep(0.1)

asyncio.create_task(manage_movements())

async def manage_smoothupdates():
    while True:
        if redis_client.set(f"lock:smoothupdates", "locked", nx=True, ex=1):
            print("lock obtained for smoothupdates")
            items = redis_client.zrange('smoothupdates', 0, 0, withscores=True)
            if len(items) > 0:
                (username, score) = items[0]
                current_time = datetime.now().timestamp()
                if current_time > float(score):
                    redis_client.zrem("smoothupdates", username)
                    def lerp(a, b, t):
                        return a + (b - a) * t
                    x = int(redis_client.hget(f"item:{username}", "x"))
                    y = int(redis_client.hget(f"item:{username}", "y"))
                    smoothX = float(redis_client.hget(f"item:{username}", "smoothX"))
                    smoothY = float(redis_client.hget(f"item:{username}", "smoothY"))
                    if abs(x-smoothX)>0.1 or abs(y-smoothY)>0.1:
                        f = int(redis_client.hget(f"item:{username}", "f"))
                        f = (f + 1) % 20
                        redis_client.hset(f"item:{username}", "f", f)
                    smoothX = lerp(smoothX, x, 0.15)
                    smoothY = lerp(smoothY, y, 0.15)
                    redis_client.hset(f"item:{username}", "smoothX", smoothX)
                    redis_client.hset(f"item:{username}", "smoothY", smoothY)
                    current_time = datetime.now()
                    future_time = current_time + timedelta(seconds=0.02)
                    timestamp = str(future_time.timestamp())
                    redis_client.zadd("smoothupdates", {username: timestamp})
            redis_client.delete(f"lock:smoothupdates")
        await asyncio.sleep(0.01)

asyncio.create_task(manage_smoothupdates())

async def handle_messages(websocket: WebSocket, username: str):
    try:
        while True:
            data = await websocket.receive_text()
            if "right" in data.lower():
                redis_client.hset(f"item:{username}", "n", 1)
            elif "down" in data.lower():
                redis_client.hset(f"item:{username}", "n", 2)
            elif "left" in data.lower():
                redis_client.hset(f"item:{username}", "n", 3)
            elif "up" in data.lower():
                redis_client.hset(f"item:{username}", "n", 4)
            print(data)
    except WebSocketDisconnect:
        print(f"{username} handle_messages disconnected")

async def send_updates(websocket: WebSocket, username: str):
    try:
        while True:
            content = {username: redis_client.hgetall(f"item:{username}")}
            for val in redis_client.keys("item:*"):
                store = redis_client.hgetall(val)
                content[store["username"]] = store
            await websocket.send_json({"type":"gamestate","sender":instance_id,"content":content})
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        print(f"{username} send_updates disconnected")

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

def random_location():
    open_spaces = [(i,j) for i in range(len(maze[0])) for j in range(len(maze)) if maze[j][i] == 0 ]
    return random.choice(open_spaces)