from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MessageBuilder:
    def __init__(self):
        self.name = None
        self.header = None
        self.body = None
        self.footer = None
        self.hour = None
        self.minute = None
        self.day = None
        self.buttons = InlineKeyboardBuilder()
        self.media = []

    async def set_name(self, name: str):
        """Add name to scheduler"""
        self.name = name

    async def set_header(self, header: str):
        """Add header."""
        self.header = header

    async def set_body(self, body: str):
        """Add body."""
        self.body = body

    async def set_footer(self, footer: str):
        """Add footer."""
        self.footer = footer

    async def add_button(self, text: str, url: str = None, callback_data: str = None):
        """Add button (url or callback)."""
        if url:
            self.buttons.add(InlineKeyboardButton(text=text, url=url))
        elif callback_data:
            self.buttons.add(InlineKeyboardButton(text=text, callback_data=callback_data))

    async def add_media(self, media_type: str, media: str, caption: str = None):
        """
        Add media (photo, video).

        :param media_type: Type of media ("photo" or "video").
        :param media: URL or file_id of media.
        :param caption: Description for media(Optional).
        """
        if media_type == "photo":
            self.media.append(InputMediaPhoto(media=media, caption=caption))
        elif media_type == "video":
            self.media.append(InputMediaVideo(media=media, caption=caption))
        else:
            raise ValueError("Unsupported media type. Use 'photo' or 'video'.")

    async def add_scheduler(self, **kwargs: any):
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

    async def get_name(self):
        """Return name."""
        return self.name

    async def get_header(self):
        """Return header."""
        return self.header

    async def get_body(self):
        """Return body."""
        return self.body

    async def get_footer(self):
        """Return footer."""
        return self.footer

    async def build_message(self):
        """Build message like a dictionary."""
        parts = []
        if self.header:
            parts.append(self.header)
        if self.body:
            parts.append(self.body)
        if self.footer:
            parts.append(self.footer)
        text = "\n\n".join(parts)
        return {"text": text, "reply_markup": self.buttons, "media": self.media}
