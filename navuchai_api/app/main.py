from fastapi import FastAPI


from app.config import engine
from app.models import Base
from app.routes import (
    tests, questions, user, auth, profile,
    category, locale, files, role, user_groups,
    test_access, test_status, results, question_type,
    test_access_status, courses, modules, lessons, enrollment, module_tests,
    test_import, analytics_views, test_group, faq, faq_categories
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

app.include_router(tests)
app.include_router(questions)
app.include_router(auth)
app.include_router(user)
app.include_router(profile)
app.include_router(category)
app.include_router(locale)
app.include_router(files)
app.include_router(role)
app.include_router(user_groups)
app.include_router(test_access)
app.include_router(test_status)
app.include_router(results)
app.include_router(courses)
app.include_router(modules)
app.include_router(lessons)
app.include_router(enrollment)
app.include_router(module_tests)
app.include_router(question_type)
app.include_router(test_access_status)
app.include_router(test_import)
app.include_router(analytics_views)
app.include_router(test_group)
app.include_router(faq)
app.include_router(faq_categories)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
