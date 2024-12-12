from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MessageBuilder:
    def __init__(self):
        self.name = None
        self.text = None
        self.footer = None
        self.hour = None
        self.minute = None
        self.day = None
        self.buttons = InlineKeyboardBuilder()
        self.buttons_count = 0
        self.media = []

    async def set_name(self, text: str):
        """Add name to scheduler"""
        self.name = text
        return self.name

    async def set_text(self, text: str):
        """Add text."""
        self.text = text
        return self.text

    async def set_footer(self, text: str):
        """Add footer."""
        self.footer = text
        return self.footer

    async def add_button(self, text: str, url: str = None, callback_data: str = None):
        """Add button (url or callback)."""
        if url:
            self.buttons.add(InlineKeyboardButton(text=text, url=url))
        elif callback_data:
            self.buttons.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        self.buttons_count += 1


    async def add_media(self, media_type: str, media: str):
        """
        Add media (photo, video).

        :param media_type: Type of media ("photo" or "video").
        :param media: URL or file_id of media.
        """
        if media_type == "photo":
            self.media.append(InputMediaPhoto(media=media))
        elif media_type == "video":
            self.media.append(InputMediaVideo(media=media))
        else:
            raise ValueError("Unsupported media type. Use 'photo' or 'video'.")

    async def set_scheduler(self, **kwargs: any):
        """Add scheduler.
        :param kwargs: Keyword arguments for scheduler. Must be any of: day, hour, minute.
        """
        if not any(key in kwargs for key in ['day', 'hour', 'minute']):
            raise ValueError("'day', 'hour' or 'minute' must be provided.")
        for key in kwargs.keys():
            if key == "day":
                self.day = kwargs['day']
            elif key == "hour":
                self.hour = kwargs['hour']
            elif key == "minute":
                self.minute = kwargs['minute']

    async def get_name(self) -> str|None:
        """Return scheduler name."""
        return self.name

    async def get_text(self) -> str|None:
        """Return text."""
        return self.text

    async def get_footer(self) -> str|None:
        """Return footer."""
        return self.footer

    async def get_buttons(self):
        """Return buttons."""
        return self.buttons.as_markup()

    async def get_buttons_len(self):
        return self.buttons_count

    async def get_media(self) -> list[str]:
        """Return media."""
        return self.media

    async def get_scheduler(self) -> tuple:
        """Return scheduler."""
        return self.day, self.hour, self.minute

    async def build_message(self) -> dict|str:
        """Build message like a dictionary."""
        parts = []
        if self.footer:
            parts.append(self.footer)
        if self.text:
            parts.append(self.text)
            text = "".join(parts)
            return {"text": text, "reply_markup": self.buttons, "media": self.media}
        else:
            return 'Error'

    async def clear_media(self, media=None):
        """Clear media.
        :param media: Media id to clear."""
        if media:
            ...
        else:
            self.media = []

    async def clear_buttons(self):
        """Clear buttons."""
        self.buttons = InlineKeyboardBuilder()

    async def clear(self):
        """Clear message."""
        self.name = None
        self.text = None
        self.footer = None
        self.media = None
        self.buttons = InlineKeyboardBuilder()
        self.hour = None
        self.minute = None


msg_builder = MessageBuilder()
