from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from Bot import dialogs
from Database.database import db

class CheckInAdminListMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.admin_users = []

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        user_id = data["event_from_user"].id
        users = db.query(query="SELECT user_id FROM white_list WHERE admin=true", fetch='fetchall')
        self.admin_users = [item for tup in users for item in tup]
        if user_id in self.admin_users:
            return await handler(event, data)
        else:
            try:
                return await event.message.answer(
                    dialogs.RU_ru['not_admin'].format(user_id),
                    parse_mode='HTML', show_alert=False
                )
            except:
                return await event.answer(
                    dialogs.RU_ru['not_admin'].format(user_id),
                    parse_mode='HTML', show_alert=False
                )


class CheckInWhiteListMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.white_users = []

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        user_id = data["event_from_user"].id
        users = db.query(query="SELECT user_id FROM white_list", fetch='fetchall')
        self.white_users = [item for tup in users for item in tup]
        if user_id in self.white_users:
            return await handler(event, data)
        else:
            try:
                return await event.message.answer(
                    dialogs.RU_ru['/start_unsuccessful'] +
                    f'\n\n<i>Ваш ID: <code>{user_id}</code></i>',
                    parse_mode='HTML'
                )
            except:
                return await event.answer(
                    dialogs.RU_ru['/start_unsuccessful'] +
                    f'\n\n<i>Ваш ID: <code>{user_id}</code></i>',
                    parse_mode='HTML'
                )


class CheckInEmployeeListMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.emloyee_users = []

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        user_id = data["event_from_user"].id
        users = db.query(query="SELECT user_id FROM employee_list", fetch='fetchall')
        self.emloyee_users = [item for tup in users for item in tup]
        if user_id in self.emloyee_users:
            return await handler(event, data)
        else:
            try:
                return await event.message.answer(
                    dialogs.RU_ru['not_employee'],
                    parse_mode='HTML'
                )
            except:
                return await event.answer(
                    dialogs.RU_ru['not_employee'],
                    parse_mode='HTML'
                )
