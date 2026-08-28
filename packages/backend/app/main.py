from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import connect_db, disconnect_db

app = FastAPI()



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def root(item_id: int):
    return {"item_id": item_id}