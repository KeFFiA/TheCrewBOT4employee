import calendar
import io
import random
import string
from datetime import datetime
from fuzzywuzzy import process

import qrcode

from prettytable import PrettyTable
import pandas as pd


from Bot import dialogs
from Bot.Utils.logging_settings import iiko_api_logger
from Database.database import db


async def attendance_sum(date_from_list, date_to_list, date_to):
    try:
        total_difference = 0

        for time1, time2 in zip(date_from_list, date_to_list):
            dt1 = datetime.fromisoformat(time1)
            dt2 = datetime.fromisoformat(time2)

            difference = dt2 - dt1
            total_difference += difference.total_seconds()

        hours, remainder = divmod(total_difference, 3600)
        minutes, _ = divmod(remainder, 60)

        result = f"{int(hours)}:{int(minutes):02}"

        dates1 = [datetime.fromisoformat(date) for date in date_from_list]
        dates2 = [datetime.fromisoformat(date) for date in date_to_list]

        time_diff_dict = {}
        for dt1, dt2 in zip(dates1, dates2):
            time_diff = (dt2 - dt1).total_seconds() / 60  # Разница в минутах
            time_diff_dict[dt1.date()] = time_diff

        start_date = min(dates1 + dates2).date()
        end_date = date_to.date()
        date_range = pd.date_range(start=start_date, end=end_date).date

        table = PrettyTable()
        table.field_names = [dialogs.RU_ru['table']['date'], dialogs.RU_ru['table']['completed']]

        for date in date_range:
            if date in time_diff_dict:
                diff = time_diff_dict[date]
                hours = int(diff // 60)
                minutes = int(diff % 60)
                table.add_row([date.strftime("%d.%m"), f"{hours}:{minutes:02d}"])
            else:
                table.add_row([date.strftime("%d.%m"), '—'])

        table.add_row([dialogs.RU_ru['table']['total'], result])

        table_for_print = f"""```{dialogs.RU_ru['table']['table']}
{table}```"""
        return table_for_print, result
    except ValueError:
        table_for_print = f"""```{dialogs.RU_ru['table']['table']}
{dialogs.RU_ru['table']['error']}```"""
        result = dialogs.RU_ru['table']['error']
        return table_for_print, result


async def get_date_range(data):
    now = datetime.now()

    if data == 'first_half':
        date_from, date_to = now.replace(day=1), now.replace(day=15)

        return date_from, date_to

    if data == 'second_half':
        if now.month == 1:
            date_from, date_to = now.replace(year=now.year - 1, month=12, day=15), now.replace(year=now.year - 1, month=12, day=31)
        else:
            date_from = now.replace(month=now.month - 1, day=16)
            date_to = now.replace(month=now.month - 1, day=1)
            date_to = date_to.replace(day=calendar.monthrange(date_from.year, date_to.month)[1])

        return date_from, date_to

    if data == 'this_month':
        date_from, date_to = now.replace(day=1), now

        return date_from, date_to

    if data == 'last_month':
        if now.month == 1:
            date_from, date_to = now.replace(year=now.year - 1, month=12, day=1), now.replace(year=now.year - 1, month=12, day=31)
        else:
            date_from = now.replace(month=now.month - 1, day=1)
            date_to = date_from.replace(day=calendar.monthrange(date_from.year, date_from.month)[1])

        return date_from, date_to


async def generate_card(user_id):
    characters = string.ascii_letters + string.digits + "=!"
    random_string = f'{user_id}_'+''.join(random.choice(characters) for _ in range(30))
    db.query(query="UPDATE customers SET card_number=%s, card_track=%s WHERE user_id=%s",
             values=(random_string, random_string, user_id))

    return random_string, random_string

async def generate_qr_card(card_number):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(card_number)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    byte_io = io.BytesIO()
    img.save(byte_io, format='PNG')
    byte_io.seek(0)

    return byte_io.getvalue()


async def find_referrer_name(guest_id):
    try:
        name, surname, middlename = db.query(query='SELECT name, surname, middlename FROM customers WHERE guest_id=%s',
                                             values=(guest_id,), fetch='fetchone')
        if middlename is None:
            name_text = f'{surname} {name}'
        else:
            name_text = f'{surname} {name} {middlename}'

        return name_text
    except:
        return dialogs.RU_ru['empty']


async def get_wallet_balance(user_info):
    try:
        for wallet_info in user_info['wallets']:
            if wallet_info['name'] == 'STAFF':
                wallet = wallet_info['balance']
                wallet_result = wallet - 15000
                if wallet_result < 0:
                    wallet_result = wallet_result * -1
                else:
                    wallet_result = 0
                return wallet_result
            else:
                return dialogs.RU_ru['error_wallet']
    except Exception as _ex:
        iiko_api_logger.error(f'Get wallet[{user_info}] balance error: {_ex}', exc_info=_ex)
        return 0


async def normalize_phone_number(phone):
    phone = ''.join(filter(str.isdigit, phone))

    if phone.startswith('8'):
        phone = '7' + phone[1:]
    elif phone.startswith('+7'):
        phone = '7' + phone[2:]
    elif phone.startswith('7'):
        phone = phone

    return phone

def find_similar_names(name, threshold=60):
    names = db.query(query='SELECT name FROM employee_server', fetch='fetchall')
    names_list = [name[0] for name in names]
    similar_names = process.extract(name, names_list, limit=5, scorer=process.fuzz.token_sort_ratio)
    result = [name for name, score in similar_names if score >= threshold]
    if result:
        return result
    else:
        return False


async def formatting_text(entities, message):
    formatted_parts = []
    last_offset = 0

    entities.sort(key=lambda e: e.offset)

    for entity in entities:
        offset = entity.offset
        length = entity.length
        text_segment = message[offset:offset + length]

        if last_offset < offset:
            formatted_parts.append(message[last_offset:offset])

        if entity.type == 'bold':
            formatted_parts.append(f'<b>{text_segment}</b>')
        elif entity.type == 'italic':
            formatted_parts.append(f'<i>{text_segment}</i>')
        elif entity.type == 'underline':
            formatted_parts.append(f'<u>{text_segment}</u>')
        elif entity.type == 'strikethrough':
            formatted_parts.append(f'<s>{text_segment}</s>')
        elif entity.type == 'code':
            formatted_parts.append(f'<code>{text_segment}</code>')
        elif entity.type == 'spoiler':
            formatted_parts.append(f'<tg-spoiler>{text_segment}</tg-spoiler>')
        elif entity.type == 'text_link':
            formatted_parts.append(f'<a href="{entity.url}">{text_segment}</a>')
        elif entity.type == 'pre':
            formatted_parts.append(f'<pre>{text_segment}</pre>')
        elif entity.type == 'blockquote':
            formatted_parts.append(f'<blockquote>{text_segment}</blockquote>')

        last_offset = offset + length

    if last_offset < len(message):
        formatted_parts.append(message[last_offset:])

    formatted_text = ''.join(formatted_parts)
    return formatted_text


