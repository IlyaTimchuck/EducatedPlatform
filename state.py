from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    get_info_user = State()
    registration_user = State()

class AddUsers(StatesGroup):
    choose_course = State()
    get_course_tittle = State()
    get_list_users = State()

class AddTask(StatesGroup):
    choose_course = State()
    choose_block = State()
    choose_options = State()
    get_task_title = State()
    get_video = State()
    get_abstract = State()
    verification = State()
    get_homework = State()


class MappingExercise(StatesGroup):
    mapping_task = State()
    solving_homework = State()