from .command import router as command_router
from .registrarion import router as registration_router
from .callbacks import router as callbacks_router
from .command_menu_admin import router as admin_router

def setup_routers(dp):
    dp.include_router(command_router)
    dp.include_router(registration_router)
    dp.include_router(callbacks_router)
    dp.include_router(admin_router)