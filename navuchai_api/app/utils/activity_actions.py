from typing import Final, Set


# Базовый whitelist кодов действий (можно дополнять по мере необходимости)
LOGIN_SUCCESS: Final[str] = "login_success"
LOGIN_FAILED: Final[str] = "login_failed"
REGISTER: Final[str] = "register"

COURSE_ENROLLED: Final[str] = "course_enrolled"
COURSE_UNENROLLED: Final[str] = "course_unenrolled"
COURSE_STARTED: Final[str] = "course_started"

LESSON_COMPLETED: Final[str] = "lesson_completed"
LESSON_OPENED: Final[str] = "lesson_opened"

TEST_COMPLETED: Final[str] = "test_completed"
TEST_STARTED: Final[str] = "test_started"


ALLOWED_ACTIONS: Final[Set[str]] = {
    LOGIN_SUCCESS,
    LOGIN_FAILED,
    REGISTER,
    COURSE_ENROLLED,
    COURSE_UNENROLLED,
    COURSE_STARTED,
    LESSON_COMPLETED,
    LESSON_OPENED,
    TEST_COMPLETED,
    TEST_STARTED,
}


