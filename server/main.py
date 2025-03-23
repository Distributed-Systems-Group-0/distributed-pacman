from fastapi import FastAPI, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import redis
import json

load_dotenv()
MONGO_USERNAME = os.getenv('MONGO_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD',"132.164.200.4")
redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")
redis_client = redis.Redis(host=redis_host, port=6379, db=0, password=redis_password)


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
app = FastAPI(lifespan=lifespan)

#Mount setup to let FastAPI know the the file directory sketch.js and style.css is in
# index.html now contains the file path to let fastapi know to load files from e.g. static/style.css
app.mount("/static", StaticFiles(directory="UI"), name="static")

#Runs front-end HTML
@app.get("/")
async def root():
    return FileResponse("UI/index.html")

#Retrieves Pac-Man's position. Will be the main function to build off of
@app.post("/api/{username}/position")
async def receive_position(request: Request, username):
    playerLocation = await request.json()
    playerLocation_json = json.dumps(playerLocation)
    redis_client.setex(f"item_{username}", 5, playerLocation_json)
    #print(f"Pac-Man position: x={playerLocation.get('x')} y={playerLocation.get('y')}")
    return {"status": "received"}