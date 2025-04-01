import random
import string
import asyncio
from aiohttp import ClientSession, BasicAuth
from transliterate import translit

import config
from Database.database import db


async def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.ascii_uppercase
    return ''.join(random.choice(characters) for _ in range(length))


async def add_user_to_group(username: str, group: str):
    url = f"{config.nextcloud_url}/ocs/v1.php/cloud/users/{username}/groups"
    headers = {
        "OCS-APIREQUEST": "true",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"groupid": group}
    async with ClientSession() as session:
        async with session.post(
            url,
            auth=BasicAuth(config.nextcloud_admin, config.nextcloud_admin_password),
            headers=headers,
            data=data
        ) as response:
            if response.status != 200:
                print(f"Failed to add user {username} to group {group}: {await response.text()}")
                return False
            else:
                print(f"User {username} added to group {group}")
                return True

async def set_manager(username: str, manager: str):
    """
    Примечание:
    Стандартный Nextcloud не имеет поля 'manager'. Этот запрос будет работать только
    если у вас установлено кастомное расширение или настроена поддержка данного атрибута.
    """
    url = f"{config.nextcloud_url}/ocs/v1.php/cloud/users/{username}"
    headers = {
        "OCS-APIREQUEST": "true",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "manager": manager
    }
    async with ClientSession() as session:
        async with session.patch(
            url,
            auth=BasicAuth(config.nextcloud_admin, config.nextcloud_admin_password),
            headers=headers,
            data=data
        ) as response:
            if response.status != 200:
                print(f"Failed to set manager for user {username}: {await response.text()}")
                return False
            else:
                print(f"Manager {manager} set for user {username}")
                return True

async def register_user(input_data: dict):
    headers = {
        "OCS-APIREQUEST": "true",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    password = await generate_random_password()
    login = translit(second_name, 'ru', reversed=True) + '_' + translit(name, 'ru', reversed=True)
    data = {
        "userid": login,
        "password": password,
        "user_name": input_data["name"],
        "user_surname": input_data["second_name"],
        "email": input_data["email"],
        "phone": input_data["phone"],
        "language": input_data["language"],
        "locale": input_data["locale"],
    }

    async with ClientSession() as session:
        async with session.post(
            url=f"{config.nextcloud_url}/ocs/v1.php/cloud/users",
            auth=BasicAuth(config.nextcloud_admin, config.nextcloud_admin_password),
            headers=headers,
            data=data
        ) as response:
            if response.status != 200:
                print(f"Failed to register user: {input_data['email']}, {await response.text()}")
                return False
            else:
                print(f"Successfully registered user: {input_data['email']}")
                print(f"Username: {login}, Temporary Password: {password}")

    if "groups" in input_data:
        for group in input_data["groups"]:
            await add_user_to_group(login, group)

    if "manager" in input_data:
        await set_manager(login, input_data["manager"])

    return True


if __name__ == "__main__":
    name, second_name, email, phone = db.query("SELECT name, surname, email, phone FROM customers WHERE user_id = %s", values=(405737823,), fetch="all")[0]
    asyncio.run(register_user({
        "name": name,
        "second_name": second_name,
        "email": email,
        "phone": phone,
        "groups": ["TheCrew (2)", "Энергия"],
        "manager": "olesyaogienko@bk.ru",
        "language": "ru",   # Также не поддерживается стандартным API
        "locale": "ru_RU",    # Также не поддерживается стандартным API
    }))
