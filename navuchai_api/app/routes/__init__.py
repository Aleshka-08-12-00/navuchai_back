from app.routes.auth import router as auth_router
from app.routes.tests import router as tests_router
from app.routes.questions import router as questions_router
from app.routes.user import router as user_router
from app.routes.profile import router as profile_router
from app.routes.category import router as category_router
from app.routes.locale import router as locale_router
from app.routes.files import router as files_router
from app.routes.role import router as role_router
from app.routes.user_groups import router as user_groups_router
from app.routes.test_access import router as test_access_router
from app.routes.test_status import router as test_status_router
from app.routes.results import router as results_router
from app.routes.question_type import router as question_type_router
from app.routes.test_access_status import router as test_access_status_router
from app.routes.courses import router as courses_router
from app.routes.modules import router as modules_router
from app.routes.lessons import router as lessons_router
from app.routes.enrollment import router as enrollment_router
from app.routes.module_tests import router as module_tests_router

auth = auth_router
tests = tests_router
questions = questions_router
user = user_router
profile = profile_router
category = category_router
locale = locale_router
files = files_router
role = role_router
user_groups = user_groups_router
test_access = test_access_router
test_status = test_status_router
results = results_router
question_type = question_type_router
test_access_status = test_access_status_router
courses = courses_router
modules = modules_router
lessons = lessons_router
enrollment = enrollment_router
module_tests = module_tests_router
