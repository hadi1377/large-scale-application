from fastapi import FastAPI
from database import engine, Base
from models import User

app = FastAPI(title="User Service")


@app.on_event("startup")
async def startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"service": "user-service"}

