from app.bot.handlers.command import router as command_router
from app.bot.handlers.registration import router as registration_router
from app.bot.handlers.admin import setup_admin_router
from app.bot.handlers.student import setup_student_router

def setup_handlers_router(dp):
    dp.include_router(command_router)
    dp.include_router(registration_router)
    setup_admin_router(dp)
    setup_student_router(dp)