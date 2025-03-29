import asyncio
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import redis
import json
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
MONGO_USERNAME = os.getenv('MONGO_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD',"132.164.200.4")
redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")
redis_client = redis.Redis(host=redis_host, port=6379, db=0, password=redis_password)

pubsub = redis_client.pubsub()

#MONGO DB CONNECTION
# define a lifespan method for fastapi
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)

# method for start the MongoDb Connection
async def startup_db_client(app):
    app.mongodb_client = AsyncIOMotorClient(
        "mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster0.wk2xt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    app.mongodb = app.mongodb_client.get_database("player")
    print("MongoDB connected.")

# method to close the database connection
async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")

# creating a server with python FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#Mount setup to let FastAPI know the the file directory sketch.js and style.css is in
# index.html now contains the file path to let fastapi know to load files from e.g. static/style.css
app.mount("/static", StaticFiles(directory="UI"), name="static")

#Runs front-end HTML
@app.get("/")
async def root():
    return FileResponse("UI/index.html")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        if redis_client.exists(f"connect_{username}"): return
        print(f"Creating {username} connection")
        redis_client.set(f"connect_{username}", "hello world")
        await websocket.accept()
        self.active_connections[username] = websocket
        print(f"User ({username}) connected")
        for un in redis_client.keys("item_*"):
            print(un)
            message = f"{redis_client.get(f"{un.decode('utf-8')}").decode('UTF-8')}"
            await self.active_connections[username].send_text(message)

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
            redis_client.delete(f"connect_{username}")
            print(f"Deleting {username} connection")
            print(f"User {username} disconnected")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

def pacman_update(username):
    un = username['data'].decode('utf-8')
    print(f"{un} part of the team? {un in manager.active_connections}")
    if un in manager.active_connections: return
    print(f"{un} is moving!")
    print(f"{redis_client.get(f"item_{un}").decode('UTF-8')}")
    asyncio.run(manager.broadcast(f"{redis_client.get(f"item_{un}").decode('UTF-8')}"))

pubsub.subscribe(**{"pacman_updates":  pacman_update})
pubsub.run_in_thread(sleep_time=0.001)

@app.websocket("/ws/location/{username}")
async def receive_player_location(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            # print(data)
            redis_client.set(f"item_{username}", data)
            redis_client.publish('pacman_updates', username)
            await manager.broadcast(f"{data}")
            
    except WebSocketDisconnect:
        manager.disconnect(username)
        # await manager.broadcast(f"Client #{username} left the game")
            