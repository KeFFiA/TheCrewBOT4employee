import hashlib
import json
import xmltodict

from aiohttp import ClientSession
from Database.database import db
from Bot.Utils.logging_settings import iiko_api_logger
from Scripts.scripts import attendance_sum, get_date_range


async def iiko_login(org_name):
    path, port, login, password = db.query(query="SELECT path, port, login, password FROM iiko_login WHERE org_name=%s",
                                           values=(org_name,), fetch='fetchone')
    password_hex = hashlib.sha1(password.encode()).hexdigest()

    url = 'https://{path}:{port}/resto/api/auth?login={login}&pass={password}'.format(path=path, port=port,
                                                                                          login=login, password=password_hex)
    async with ClientSession() as session:
        async with session.get(url=url) as resp:
            status = resp.status
            if status == 200:
                db.query('UPDATE iiko_login SET token=%s WHERE org_name=%s', (await resp.text(), org_name))
                return resp.status, 'Ok'
            else:
                return resp.status, resp.reason


async def iiko_logout(org_name):
    path, port, token = db.query(query="SELECT path, port, token FROM iiko_login WHERE org_name=%s", values=(org_name,),
                                 fetch='fetchone')
    url = 'https://{path}:{port}/resto/api/logout?key={key}'.format(path=path, port=port, key=token)
    async with ClientSession() as session:
        async with session.get(url=url) as resp:
            if resp.status == 200:
                db.query(query="UPDATE iiko_login SET token='' WHERE org_name=%s", values=(org_name,))
                return resp.status, 'Ok'
            else:
                return resp.status, resp.reason


async def update_employees():
    org_names = db.query(query="SELECT org_name FROM iiko_login", fetch='fetchall')[0]
    for org_name in org_names:
        status, reason = await iiko_login(org_name)
        if status == 200:
            path, port, key = db.query(query="SELECT path, port, token FROM iiko_login WHERE org_name=%s", values=(org_name,),
                                       fetch='fetchone')
            url = 'https://{path}:{port}/resto/api/employees'.format(path=path, port=port)
            params = {'key': key, 'includeDeleted': 'False'}
            async with ClientSession() as session:
                async with session.get(url=url, params=params) as resp:
                    status = resp.status
                    if status == 200:
                        response_data = json.dumps(xmltodict.parse(await resp.text()), sort_keys=True, indent=4, ensure_ascii=False)
                        data = json.loads(response_data)
                        employees_list = data['employees']['employee']
                        for employee in employees_list:
                            name = employee.get('name', None)
                            id = employee.get('id', None)
                            role = employee.get('mainRoleCode', None)
                            db.query(query="INSERT INTO employee_server (org_name, employee_id, name, role) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                                     values=(org_name, id, name, role))
                        status, reason = await iiko_logout(org_name)
                        if status != 200:
                            iiko_api_logger.critical(f'Logout failed. Organization name: {org_name}. Status: {status}. Reason: {reason}')
        else:
            iiko_api_logger.critical(f'Login failed. Organization name: {org_name}. Status: {status}. Reason: {reason}')


async def employees_attendance(user_id, data):
    org_name, path, port = db.query(query="""SELECT il.org_name, il.path, il.port
                                FROM employee_list el
                                JOIN employee_server es ON el.emp_id = es.employee_id     
                                JOIN iiko_login il ON es.org_name = il.org_name 
                                WHERE el.user_id = %s""", values=(user_id,), fetch='fetchone')
    status, reason = await iiko_login(org_name)
    if status == 200:
        emp_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", values=(user_id,), fetch='fetchone')[0]
        key = db.query(query="SELECT token FROM iiko_login WHERE org_name=%s", values=(org_name,), fetch='fetchone')[0]
        url = 'https://{path}:{port}/resto/api/employees/attendance/byEmployee/{employee_id}'.format(path=path, port=port,
                                                                                                     employee_id=emp_id)
        date_from, date_to = await get_date_range(data)
        params = {
            'key': key,
            'from': date_from.strftime('%Y-%m-%d'),
            'to': date_to.strftime('%Y-%m-%d'),
            'withPaymentDetails': 'false',
        }
        async with ClientSession() as session:
            async with session.get(url=url, params=params) as resp:
                status = resp.status
                if status == 200:
                    response_data = json.dumps(xmltodict.parse(await resp.text()), sort_keys=True, indent=4,
                                               ensure_ascii=False)
                    data = json.loads(response_data)
                    date_from_list = []
                    date_to_list = []
                    try:
                        for attendance in data['attendances']['attendance']:
                            try:
                                date_from_list.append(attendance['dateFrom'])
                                date_to_list.append(attendance['dateTo'])
                            except TypeError:
                                pass
                    except:
                        try:
                            attendance = data['attendances']['attendance']
                            date_from_list.append(attendance['dateFrom'])
                            date_to_list.append(attendance['dateTo'])
                        except TypeError:
                            pass
                    status, reason = await iiko_logout(org_name)
                    if status != 200:
                        iiko_api_logger.critical(
                            f'Logout failed. Organization name: {org_name}. Status: {status}. Reason: {reason}')
                        return 'Error'
                    return await attendance_sum(date_from_list, date_to_list, date_to)
                else:
                    iiko_api_logger.error(f'Fetch employee attendance failed. Organization name: {org_name}. Status: {status}. Reason: {resp.reason}')
                    return 'Error'
    else:
        iiko_api_logger.critical(f'Login failed. Organization name: {org_name}. Status: {status}. Reason: {reason}')
        return 'Error'


