from typing import Final, Set, Dict


# Базовый whitelist кодов действий (можно дополнять по мере необходимости)
LOGIN_SUCCESS: Final[str] = "login_success"
LOGIN_FAILED: Final[str] = "login_failed"
REGISTER: Final[str] = "register"

COURSE_ENROLLED: Final[str] = "course_enrolled"
COURSE_UNENROLLED: Final[str] = "course_unenrolled"
COURSE_STARTED: Final[str] = "course_started"
COURSE_COMPLETED: Final[str] = "course_completed"

LESSON_COMPLETED: Final[str] = "lesson_completed"
LESSON_OPENED: Final[str] = "lesson_opened"
MODULE_COMPLETED: Final[str] = "module_completed"

TEST_COMPLETED: Final[str] = "test_completed"
TEST_STARTED: Final[str] = "test_started"


ALLOWED_ACTIONS: Final[Set[str]] = {
    LOGIN_SUCCESS,
    LOGIN_FAILED,
    REGISTER,
    COURSE_ENROLLED,
    COURSE_UNENROLLED,
    COURSE_STARTED,
    COURSE_COMPLETED,
    LESSON_COMPLETED,
    LESSON_OPENED,
    MODULE_COMPLETED,
    TEST_COMPLETED,
    TEST_STARTED,
}

# Словарь русских названий действий
ACTION_RU_NAMES: Final[Dict[str, str]] = {
    LOGIN_SUCCESS: "Успешный вход",
    LOGIN_FAILED: "Неуспешный вход",
    REGISTER: "Регистрация",
    COURSE_ENROLLED: "Запись на курс",
    COURSE_UNENROLLED: "Отмена записи на курс",
    COURSE_STARTED: "Начало курса",
    COURSE_COMPLETED: "Завершение курса",
    LESSON_COMPLETED: "Завершение урока",
    LESSON_OPENED: "Открытие урока",
    MODULE_COMPLETED: "Завершение модуля",
    TEST_COMPLETED: "Завершение теста",
    TEST_STARTED: "Начало теста",
}


