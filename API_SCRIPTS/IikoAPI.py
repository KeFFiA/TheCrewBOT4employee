import json
import os

from aiohttp import ClientSession
from Database.database import db
from Bot.Utils.logging_settings import iiko_api_logger
from path import bot_temp_path
from config import IIKO_TOKEN

try:
    if os.path.exists(bot_temp_path):
        pass
    else:
        os.mkdir(bot_temp_path)
    path_token = os.path.join(bot_temp_path, 'iiko_token.json')
    open(path_token, 'a').close()
except Exception as _ex:
    iiko_api_logger.critical(f'Error opening json: {_ex}')


async def update_token():
    url = 'https://api-ru.iiko.services/api/1/access_token'
    try:

        async with ClientSession() as session:
            async with session.post(url=url, json=IIKO_TOKEN) as resp:
                text = await resp.json()
                data = {
                    'Authorization': f'Bearer {text['token']}'
                }
        try:
            with open(path_token, 'w') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            await update_organizations()
        except Exception as _ex:
            iiko_api_logger.critical(f'Error writing token: {_ex}')
            return False
    except Exception as _ex:
        iiko_api_logger.critical(f'Error updating token: {_ex}')
        return False


async def update_organizations():
    url = 'https://api-ru.iiko.services/api/1/organizations'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
            headers = {
                'Authorization': token['Authorization']
            }
        except Exception as _ex:
            iiko_api_logger.critical(f'Error reading token: {_ex}')
            return False
        async with ClientSession() as session:
            async with session.post(url=url, headers=headers, json={}) as resp:
                data = await resp.json()
                try:
                    for organization in data.get('organizations', []):
                        db.query(query="INSERT INTO organizations (name, org_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                                 values=(organization['name'], organization['id']))
                    await update_couriers()
                except Exception as _ex:
                    iiko_api_logger.critical(f'Error updating organizations: {_ex}')
                    return False
    except Exception as _ex:
        iiko_api_logger.critical(f'Error updating organizations: {_ex}')
        return False


async def update_couriers():
    url = 'https://api-ru.iiko.services/api/1/employees/couriers'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
                org_ids = list(db.query(query="SELECT org_id FROM organizations", fetch='fetchall'))
                organization_ids = []
                for org_id in org_ids:
                    org_id = org_id[0]
                    organization_ids.append(org_id)
                params = {
                    'organizationIds': organization_ids
                }
        except Exception as _ex:
            iiko_api_logger.critical(f'Error reading token: {_ex}')
            return False
        async with ClientSession() as session:
            async with session.post(url=url, headers=token, json=params) as resp:
                data = await resp.json()
                user_dict = {}
                for org in data['employees']:
                    organization_id = org['organizationId']
                    for item in org['items']:
                        if not item['isDeleted']:
                            emp_id = item['id']
                            display_name = item['displayName']

                            if emp_id not in user_dict:
                                user_dict[emp_id] = {
                                    'name': display_name,
                                    'emp_id': emp_id,
                                    'org_ids': []
                                }
                            user_dict[emp_id]['org_ids'].append(organization_id)

                employees_list = list(user_dict.values())
                try:
                    for employee in employees_list:
                        db.query(query="INSERT INTO employee_couriers (name, employee_id, org_ids) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                 values=(employee['name'], employee['emp_id'], employee['org_ids']))
                        db.query(query="UPDATE employee_list SET emp_id=%s WHERE name=%s",
                                 values=(employee['emp_id'], employee['name']))
                    await update_terminals()
                except Exception as _ex:
                    iiko_api_logger.critical(f'Error updating employees: {_ex}', exc_info=True)
                    return False
    except Exception as _ex:
        iiko_api_logger.critical(f'Error updating couriers: {_ex}')
        return False


async def update_terminals():
    url = 'https://api-ru.iiko.services/api/1/terminal_groups'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_api_logger.critical(f'Error reading token: {_ex}')
            return False
        org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall')
        org_ids_list = []
        for org_id in org_ids:
            org_ids_list.append(org_id[0])
        params = {
            'organizationIds': org_ids_list,
            'includeDisabled': False
        }
        async with ClientSession() as session:
            async with session.post(url=url, headers=token, json=params) as resp:
                data = await resp.json()
                terminals_dict = {}

                for group in data['terminalGroups']:
                    term_ids = [item['id'] for item in group['items']]
                    org_id = group['organizationId']

                    if term_ids:
                        terminals_dict[org_id] = term_ids

                for k, v in terminals_dict.items():
                    db.query(query="UPDATE organizations SET terminal_groups=%s WHERE org_id=%s", values=(v, k))
                return True

    except Exception as _ex:
        iiko_api_logger.critical(f'Error updating terminals: {_ex}')
        return False


async def check_shift(employee_id):
    url = 'https://api-ru.iiko.services/api/1/employees/shift/is_open'
    try:
        try:
            org_ids = db.query(query="SELECT org_ids FROM employee_couriers WHERE employee_id=%s", fetch='fetchall',
                               values=(employee_id,))[0][0]

            org_ids_list = org_ids.replace('{', '').replace('}', '').split(',')

            term_ids_dict = {}
            for org_id in org_ids_list:
                term_id = db.query(query="SELECT terminal_groups FROM organizations WHERE org_id=%s", fetch='fetchall',
                                    values=(org_id,))[0][0]
                try:
                    term_id = term_id.replace('{', '').replace('}', '').split(',')
                except:
                    term_id = term_id.replace('{', '').replace('}', '')

                term_ids_dict[org_id] = term_id
            try:
                with open(path_token, 'r', encoding='utf-8') as file:
                    token = json.load(file)
            except Exception as _ex:
                iiko_api_logger.critical(f'Error reading token: {_ex}')
                return False

            for k, v in term_ids_dict.items():
                for term_id in v:
                    params = {
                        'organizationId': k,
                        'terminalGroupId': term_id,
                        'employeeId': employee_id
                    }
                    async with ClientSession() as session:
                        async with session.post(url=url, headers=token, json=params) as resp:
                            data = await resp.json()
                            if data['isSessionOpened']:
                                db.query(query='UPDATE employee_list SET term_open=%s, org_open=%s WHERE emp_id=%s',
                                         values=(term_id, k, employee_id))
                                return True
        except Exception as _ex:
            iiko_api_logger.critical(f'Error fetching data: {_ex}', exc_info=True)
            return False
    except Exception as _ex:
        iiko_api_logger.critical(f'Error checking shift: {_ex}')
        return False


async def shift_close(user_id):
    url = 'https://api-ru.iiko.services/api/1/employees/shift/clockout'
    emp_id, term_id, org_id = db.query(query="SELECT emp_id, term_open, org_open FROM employee_list WHERE user_id=%s",
                                       fetch='fetchone', values=(user_id,))
    params = {
        'organizationId': org_id,
        'terminalGroupId': term_id,
        'employeeId': emp_id
    }
    try:
        with open(path_token, 'r', encoding='utf-8') as file:
            token = json.load(file)
    except Exception as _ex:
        iiko_api_logger.critical(f'Error reading token: {_ex}')
        return False
    try:
        async with ClientSession() as session:
            async with session.post(url=url, headers=token, json=params) as resp:
                status = resp.status
                if status == 200:
                    db.query(query="UPDATE employee_list SET term_open='', org_open='' WHERE user_id=%s",
                             values=(user_id,))
                    return True
                else:
                    return False
    except Exception as _ex:
        iiko_api_logger.critical(f'Error closing shift for employee <{emp_id}>: {_ex}')
        return False


async def shift_open(user_id, org_id):
    emp_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", values=(user_id,), fetch='fetchone')[0]
    term_id = db.query(query="SELECT terminal_groups FROM organizations WHERE org_id=%s", values=(org_id,),
                       fetch='fetchone')[0]

    try:
        term_id_list = term_id.replace('{', '').replace('}', '').split(',')
        term_id_list = term_id_list[0]
    except:
        term_id_list = term_id.replace('{', '').replace('}', '')

    url = 'https://api-ru.iiko.services/api/1/employees/shift/clockin'
    params = {
        'organizationId': org_id,
        'terminalGroupId': term_id_list,
        'employeeId': emp_id
    }
    try:
        with open(path_token, 'r', encoding='utf-8') as file:
            token = json.load(file)
    except Exception as _ex:
        iiko_api_logger.critical(f'Error reading token: {_ex}')
        return False
    try:
        async with ClientSession() as session:
            async with session.post(url=url, headers=token, json=params) as resp:
                status = resp.status
                if status == 200:
                    db.query(query='UPDATE employee_list SET term_open=%s, org_open=%s WHERE user_id=%s',
                             values=(term_id_list[0], org_id, user_id))
                    return True
                else:
                    iiko_api_logger.error(f'Error opening shift for employee <{emp_id}>: {await resp.json()}')
                    return False
    except Exception as _ex:
        iiko_api_logger.critical(f'Error opening shift for employee <{emp_id}>: {_ex}')

