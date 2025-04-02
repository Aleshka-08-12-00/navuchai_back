from fastapi import FastAPI

from app.config import engine
from app.models import Base
from app.routes import tests, questions

app = FastAPI(title="Test API")

app.include_router(tests.router)
app.include_router(questions.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
