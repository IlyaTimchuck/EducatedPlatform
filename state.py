from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    get_name = State()

class AddUsers(StatesGroup):
    choose_course = State()
    get_course_tittle = State()
    get_list_users = State()

class AddTask(StatesGroup):
    choose_course = State()
    block_data = State()
    get_task_tittle = State()
    get_video = State()
    get_abstract = State()
    verification = State()
    get_homework = State()