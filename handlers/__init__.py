from .command import router as command_router
from registration import router as registration_router
from .command_menu_admin import router as admin_router
from .recording_answers import router as student_router

def setup_routers(dp):
    dp.include_router(command_router)
    dp.include_router(registration_router)
    dp.include_router(admin_router)
    dp.include_router(student_router)