from fastapi import FastAPI

from app.config import engine
from app.models import Base
from app.routes import (
    tests, questions, user, auth, profile,
    category, locale, files, role, user_groups,
    test_access, test_status
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tests.router)
app.include_router(questions.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(profile.router)
app.include_router(category.router)
app.include_router(locale.router)
app.include_router(files.router)
app.include_router(role.router)
app.include_router(user_groups.router)
app.include_router(test_access.router)
app.include_router(test_status.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
