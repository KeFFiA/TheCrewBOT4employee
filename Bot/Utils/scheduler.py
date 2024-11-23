from datetime import datetime

from apscheduler.triggers.cron import CronTrigger

from API_SCRIPTS.iiko_cloudAPI import update_token, update_menu, update_loyalty_programs, update_customer_categories
from API_SCRIPTS.iikoAPI import update_employees, employees_attendance
from Bot.Utils.logging_settings import scheduler_logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from Database.database import db


scheduler = AsyncIOScheduler()


async def update_tokens_cloud_job():
    try:
        await update_token()
        scheduler_logger.info(f"Job executed: update_tokens_cloud at {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")
    except Exception as _ex:
        scheduler_logger.error(f"Error executing job update_tokens_cloud: {_ex}")


async def update_menu_cloud_job():
    try:
        await update_menu()
        scheduler_logger.info(f"Job executed: update_menu_cloud at {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")
    except Exception as _ex:
        scheduler_logger.error(f"Error executing job update_menu_cloud: {_ex}")


async def update_employees_iiko_job():
    try:
        await update_employees()
        scheduler_logger.info(f"Job executed: update_employees_iiko at {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")
    except Exception as _ex:
        scheduler_logger.error(f"Error executing job update_employees_iiko: {_ex}")


async def update_loyalty():
    try:
        await update_loyalty_programs()
        scheduler_logger.info(f"Job executed: update_loyalty at {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")
    except Exception as _ex:
        scheduler_logger.error(f"Error executing job update_loyalty_categories: {_ex}")


async def update_customers_categories():
    try:
        await update_customer_categories()
        scheduler_logger.info(f"Job executed: update_customer_categories at {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")
    except Exception as _ex:
        scheduler_logger.error(f"Error executing job update_customer_categories: {_ex}")


async def mailing_attendance():
    now = datetime.now()
    try:
        user_ids = db.query(query="SELECT user_id FROM employee_list WHERE emp_id IS NOT NULL AND receive_shift_time IS TRUE",
                            fetch='fetchall')
        for user_id in user_ids:
            if now.day == 22:
                data = 'first_half'
                await employees_attendance(user_id=user_id[0], data=data, mailing=True)
            elif now.day == 1:
                data = 'second_half'
                await employees_attendance(user_id=user_id[0], data=data, mailing=True)
        scheduler_logger.info(f"Job executed: mailing_attendance at {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")
    except Exception as _ex:
        scheduler_logger.error(f"Error executing job send_attendance_for_users: {_ex}")


def load_jobs():
    try:
        scheduler.add_job(update_tokens_cloud_job, 'cron', hour='*', minute=0)
        scheduler.add_job(update_menu_cloud_job, 'cron', hour='*', minute=0)
        scheduler.add_job(update_employees_iiko_job, 'cron', hour='*', minute=0)
        scheduler.add_job(mailing_attendance, CronTrigger(day='1,16', hour=12, minute=0))
        scheduler.add_job(update_loyalty, 'cron', hour='*', minute=0)
        scheduler.add_job(update_customers_categories, 'cron', hour=0, minute=0)
        scheduler_logger.info('Jobs loaded correctly.')
    except Exception as _ex:
        scheduler_logger.error(f'Failed to load jobs\n{_ex}')
