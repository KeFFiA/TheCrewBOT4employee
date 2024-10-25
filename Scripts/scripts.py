import calendar
from datetime import datetime
from prettytable import PrettyTable
import pandas as pd

from Bot import dialogs


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
            date_from = now.replace(month=now.month - 1, day=15)
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

