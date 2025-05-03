from app.bot.handlers.student.homework import router as homework_router
from app.bot.handlers.student.student_menu_navigation import router as student_menu_navigation_router


def setup_student_router(dp):
    dp.include_router(homework_router)
    dp.include_router(student_menu_navigation_router)