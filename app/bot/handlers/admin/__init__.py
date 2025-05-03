from app.bot.handlers.admin.add_users import router as add_users_router
from app.bot.handlers.admin.admin_menu_navigation import router as admin_menu_navigation_router
from app.bot.handlers.admin.create_task import router as crate_task_router
from app.bot.handlers.admin.deletion_user import router as deletion_user_router

def setup_admin_router(dp):
    dp.include_router(add_users_router)
    dp.include_router(admin_menu_navigation_router)
    dp.include_router(crate_task_router)
    dp.include_router(deletion_user_router)