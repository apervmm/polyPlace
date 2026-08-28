from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import connect_db, disconnect_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(lifespan=lifespan)



@app.get("/health")
async def health():
    return {"status": "OK"}