from .create_task import router as create_task_router
from .learning import router as learning_router

def setup_routers_callbacks(dp):
    dp.include_router(create_task_router)
    dp.include_router(learning_router)
