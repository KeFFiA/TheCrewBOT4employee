from datetime import datetime

from API_SCRIPTS.Iiko_cloudAPI import update_token, update_menu
from API_SCRIPTS.iikoAPI import update_employees
from Bot.Utils.logging_settings import scheduler_logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler

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


def load_jobs():
    try:
        scheduler.add_job(update_tokens_cloud_job, 'cron', hour='*', minute=0)
        scheduler.add_job(update_menu_cloud_job, 'cron', hour='*', minute=0)
        scheduler.add_job(update_employees_iiko_job, 'cron', hour='*', minute=0)
        scheduler_logger.info('Jobs loaded correctly.')
    except Exception as _ex:
        scheduler_logger.error(f'Failed to load jobs\n{_ex}')
