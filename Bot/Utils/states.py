from aiogram.fsm.state import StatesGroup, State


class Register(StatesGroup):
    step = State()


class Choose(StatesGroup):
    choose = State()
    choose_org = State()


class Settings(StatesGroup):
    name = State()


class WhiteList(StatesGroup):
    user = State()
    choose = State()
