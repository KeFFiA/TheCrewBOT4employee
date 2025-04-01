import json
import os
from datetime import datetime

from aiohttp import ClientSession

from Bot.Utils.logging_settings import iiko_cloud_api_logger
from Database.database import db
from Database.database_query import check_stop_list, stop_list_differences
from Scripts.scripts import generate_card
from config import IIKO_TOKEN
from path import bot_temp_path

try:
    if os.path.exists(bot_temp_path):
        pass
    else:
        os.mkdir(bot_temp_path)
    path_token = os.path.join(bot_temp_path, 'iiko_token.json')
    open(path_token, 'a').close()
except Exception as _ex:
    iiko_cloud_api_logger.critical(f'Error opening json: {_ex}')


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
            iiko_cloud_api_logger.critical(f'Error writing token: {_ex}')
            return False
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error updating token: {_ex}')
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
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
            return False
        async with ClientSession() as session:
            async with session.post(url=url, headers=headers, json={}) as resp:
                data = await resp.json()
                try:
                    for organization in data.get('organizations', []):
                        db.query(
                            query="INSERT INTO organizations (name, org_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            values=(organization['name'], organization['id']), log_level=30, debug=True)
                    await update_couriers()
                except Exception as _ex:
                    iiko_cloud_api_logger.critical(f'Error updating organizations: {_ex}')
                    return False
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error updating organizations: {_ex}')
        return False


async def update_couriers():
    url = 'https://api-ru.iiko.services/api/1/employees/couriers'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
                org_ids = list(
                    db.query(query="SELECT org_id FROM organizations", fetch='fetchall', log_level=30, debug=True))
                organization_ids = []
                for org_id in org_ids:
                    org_id = org_id[0]
                    organization_ids.append(org_id)
                params = {
                    'organizationIds': organization_ids
                }
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
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
                        db.query(
                            query="INSERT INTO employee_couriers (name, employee_id, org_ids) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                            values=(employee['name'], employee['emp_id'], employee['org_ids']), log_level=30,
                            debug=True)
                    await update_terminals()
                except Exception as _ex:
                    iiko_cloud_api_logger.critical(f'Error updating employees: {_ex}', exc_info=True)
                    return False
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error updating couriers: {_ex}')
        return False


async def update_terminals():
    url = 'https://api-ru.iiko.services/api/1/terminal_groups'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
            return False
        org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall', log_level=30, debug=True)
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
        iiko_cloud_api_logger.critical(f'Error updating terminals: {_ex}')
        return False


async def update_loyalty_programs():
    url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/program'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
            return False

        org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall', log_level=30, debug=True)
        for org_id in org_ids:
            params = {
                'organizationId': org_id[0],
                'withoutMarketingCampaigns': False
            }
            async with ClientSession() as session:
                async with session.post(url=url, headers=token, json=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        programs = data['Programs']
                        marketing_camp_ids = []
                        for program in programs:
                            marketing_campaigns = program['marketingCampaigns']
                            for marketing_campaign in marketing_campaigns:
                                marketing_camp_ids.append(marketing_campaign['id'])
                            db.query(query="""
                                INSERT INTO loyalty_program (
                                    org_id, id, name, description, servicefrom, serviceto, notifyaboutbalancechanges,
                                    programtype, isactive, walletid, appliedorganizations,
                                    templatetype, haswelcomebonus, welcomebonussum, isexchangerateenabled, refilltype
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (id) DO UPDATE SET
                                        name = EXCLUDED.name,
                                        description = EXCLUDED.description,
                                        servicefrom = EXCLUDED.servicefrom,
                                        serviceto = EXCLUDED.serviceto,
                                        notifyaboutbalancechanges = EXCLUDED.notifyaboutbalancechanges,
                                        programtype = EXCLUDED.programtype,
                                        isactive = EXCLUDED.isactive,
                                        walletid = EXCLUDED.walletid,
                                        appliedorganizations = EXCLUDED.appliedorganizations,
                                        templatetype = EXCLUDED.templatetype,
                                        haswelcomebonus = EXCLUDED.haswelcomebonus,
                                        welcomebonussum = EXCLUDED.welcomebonussum,
                                        isexchangerateenabled = EXCLUDED.isexchangerateenabled,
                                        refilltype = EXCLUDED.refilltype;
                                """, values=(
                                org_id[0], program.get('id'), program.get('name'), program.get('description'),
                                program.get('serviceFrom'), program.get('serviceTo'),
                                program.get('notifyAboutBalanceChanges'),
                                program.get('programType'), program.get('isActive'), program.get('walletId'),
                                program.get('appliedOrganizations'),
                                program.get('templateType'), program.get('hasWelcomeBonus'),
                                program.get('welcomeBonusSum'), program.get('isExchangeRateEnabled'),
                                program.get('refillType')
                            ))
                            for campaign in marketing_campaigns:
                                db.query(query="""
                                        INSERT INTO loyalty_marketing_campaigns (
                                            org_id, programId, id, name, description, isActive, periodFrom,
                                            periodTo
                                        )
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                        ON CONFLICT (id) DO UPDATE SET
                                            org_id = EXCLUDED.org_id,
                                            programid = EXCLUDED.programid,
                                            id = EXCLUDED.id,
                                            name = EXCLUDED.name,
                                            description = EXCLUDED.description,
                                            isActive = EXCLUDED.isActive,
                                            periodFrom = EXCLUDED.periodFrom,
                                            periodTo = EXCLUDED.periodTo
                                        """, values=(
                                    org_id[0], campaign.get('programId'), campaign.get('id'), campaign.get('name'),
                                    campaign.get('description'),
                                    campaign.get('isActive'), campaign.get('periodFrom'), campaign.get('periodTo')
                                ))
                    else:
                        iiko_cloud_api_logger.error(
                            f'Update loyalty programs status error: {resp.status} | {await resp.text()}')
                        return False
        return True
    except Exception as _ex:
        iiko_cloud_api_logger.error(f'Update loyalty programs error: {_ex}')
        return False


async def update_customer_categories():
    url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer_category'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
            return False

        org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall')
        for org_id in org_ids:
            params = {
                'organizationId': org_id[0],
            }
            async with ClientSession() as session:
                async with session.post(url=url, headers=token, json=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        categories = data['guestCategories']
                        for category in categories:
                            db.query(query="""
                            INSERT INTO customer_categories (
                                org_id, id, name, isactive, isdefaultfornewguests) VALUES (
                                    %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET
                                    id = EXCLUDED.id,
                                    name = EXCLUDED.name,
                                    isactive = EXCLUDED.isActive,
                                    isdefaultfornewguests = EXCLUDED.isDefaultfornewguests
                            """, values=(
                                org_id[0],
                                category.get('id'),
                                category.get('name'),
                                category.get('isActive'),
                                category.get('isDefaultForNewGuests')
                            ))
                    else:
                        iiko_cloud_api_logger.error(
                            f'Update customer_categories status error: {resp.status} | {await resp.text()}')
                        return False
        return True
    except Exception as _ex:
        iiko_cloud_api_logger.error(f'Update customer_categories error: {_ex}')
        return False


async def create_update_customer(user_id):
    url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/create_or_update'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
            return False
        result = db.query(query="""SELECT guest_id, name, middlename, surname, birthday, sex, phone, email, referrer_id, 
        consent_status, receive_promo, comment, card_track, card_number
                                           FROM customers WHERE user_id=%s""", values=(user_id,),
                          fetch='fetchone')

        if result:
            guest_id, name, middle_name, surname, birthday, sex, phone, email, referrer_id, consent_status, promo, comment, card_track, card_number = (
                value if value is not None else None for value in result
            )
            if card_track is None or card_number is None:
                card_check = False
                card_track, card_number = await generate_card(user_id)
            else:
                card_check = True
            org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall')
            for org_id in org_ids:
                if card_check:
                    params = {
                        'id': guest_id,
                        'organizationId': org_id[0],
                        'phone': phone,
                        'name': name,
                        'cardTrack': card_track,
                        'cardNumber': card_number,
                        'middleName': middle_name,
                        'surName': surname,
                        'birthday': f'{datetime.strptime(birthday, "%d.%m.%Y").strftime("%Y-%m-%d 00:00:00.000")}',
                        'email': email,
                        'sex': int(sex),
                        'referrerId': referrer_id,
                        'consentStatus': int(consent_status),
                        'shouldReceivePromoActionsInfo': promo,
                        'userData': comment
                    }
                else:
                    params = {
                        'id': guest_id,
                        'organizationId': org_id[0],
                        'phone': phone,
                        'cardTrack': card_track,
                        'cardNumber': card_number,
                        'name': name,
                        'middleName': middle_name,
                        'surName': surname,
                        'birthday': f'{datetime.strptime(birthday, "%d.%m.%Y").strftime("%Y-%m-%d 00:00:00.000")}',
                        'email': email,
                        'sex': int(sex),
                        'referrerId': referrer_id,
                        'consentStatus': int(consent_status),
                        'shouldReceivePromoActionsInfo': promo,
                        'userData': comment
                    }
                async with ClientSession() as session:
                    async with session.post(url=url, headers=token, json=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            guest_id = data['id']
                            db.query(query='UPDATE customers SET guest_id = %s, category = %s WHERE user_id = %s',
                                     values=(guest_id, "FRIEND", user_id))
                            db.query(query='UPDATE users SET is_registered=TRUE WHERE user_id=%s', values=(user_id,))

                            user_check = db.query(
                                query="SELECT name FROM employee_server WHERE name ILIKE %s AND name ILIKE %s",
                                values=(f'%{surname}%', f'%{name}%'), fetch='fetchone')
                            if user_check:
                                db.query(query="""BEGIN;
                                                  INSERT INTO employee_list (emp_id, phone, user_id) 
                                                  VALUES (
                                                    (SELECT employee_id FROM employee_server WHERE name ILIKE %s AND name ILIKE %s LIMIT 1),
                                                    %s,  -- phone
                                                    %s   -- user_id
                                                  )
                                                  ON CONFLICT DO NOTHING;
                                                  UPDATE employee_list SET name=(SELECT name FROM employee_server WHERE name ILIKE %s AND name ILIKE %s LIMIT 1)
                                                  WHERE user_id=%s""",
                                         values=(
                                         f'%{surname}%', f'%{name}%', phone, user_id, f'%{surname}%', f'%{name}%',
                                         user_id))
                                db.query(query='UPDATE users SET is_employee=TRUE WHERE user_id=%s', values=(user_id,))
                                url_1 = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer_category/add'
                                staff_category_id = \
                                db.query(query='SELECT id FROM customer_categories WHERE name=%s', values=('STAFF',),
                                         fetch='fetchone')[0]
                                params_1 = {
                                    "customerId": guest_id,
                                    "categoryId": staff_category_id,
                                    "organizationId": org_id[0]
                                }
                                async with ClientSession() as session_1:
                                    async with session_1.post(url=url_1, headers=token, json=params_1) as resp_1:
                                        if resp_1.status == 200:
                                            db.query(query='UPDATE customers SET category = %s WHERE user_id = %s',
                                                     values=('STAFF', user_id))
                                            program_result = await add_customer_program(guest_id)
                                            if not program_result:
                                                iiko_cloud_api_logger.error(f'Error adding program user_id: {user_id} | error: {program_result}')
                                                return False
                                        else:
                                            data_1 = await resp_1.json()
                                            if data_1['description'] == 'Category binded to another customer':
                                                db.query(query='UPDATE customers SET category = %s WHERE user_id = %s',
                                                         values=('STAFF', user_id))
                                                program_result = await add_customer_program(guest_id)
                                                if not program_result:
                                                    iiko_cloud_api_logger.error(
                                                        f'Error adding program user_id: {user_id} | error: {program_result}')
                                                    return False
                                            else:
                                                iiko_cloud_api_logger.error(
                                                    f'Add STAFF category for [{user_id}] failed with error: {resp_1.status} | {await resp_1.text()}')
                                                return False

                        else:
                            iiko_cloud_api_logger.error(
                                f'Create customer status error: {resp.status}\n Error: {await resp.text()}')
                            return False
            return True
    except Exception as _ex:
        iiko_cloud_api_logger.error(f'Create customer[{user_id}] error: {_ex}', exc_info=True)
        return False


async def add_customer_program(guest_id):
    url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/program/add'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: \n{_ex}')
            return False

        org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall')
        prog_id = db.query(query="SELECT programid FROM loyalty_marketing_campaigns WHERE name ILIKE %s OR name ILIKE %s",
                           values=('STAFF питание', 'Стафф питание'), fetch='fetchone')[0]
        for org_id in org_ids:
            params = {
                'organizationId': org_id[0],
                'programId': prog_id,
                'customerId': guest_id,
            }
            async with ClientSession() as session:
                async with session.post(url=url, headers=token, json=params) as resp:
                    if resp.status == 200:
                        wallet_id = db.query(query='SELECT walletid FROM loyalty_program WHERE id=%s', values=(prog_id,), fetch='fetchone')[0]
                        url_1 = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/wallet/topup'
                        params_1 = {
                            "customerId": guest_id,
                            "walletId": wallet_id,
                            "sum": 5000,
                            "organizationId": org_id[0]
                        }
                        async with ClientSession() as session_1:
                            async with session_1.post(url=url_1, headers=token, json=params_1) as resp_1:
                                if resp_1.status != 200:
                                    iiko_cloud_api_logger.error(f'Popup user [{guest_id}] wallet status error: {resp_1.status} | {await resp_1.text()}')
                                    return False
                    else:
                        iiko_cloud_api_logger.error(f'Add customer to program status error: {resp.status} | {await resp.text()}')
        return True
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Add customer to program failed with error: \n{_ex}')

async def get_customer(user_id):
    url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/info'
    try:
        try:
            with open(path_token, 'r', encoding='utf-8') as file:
                token = json.load(file)
        except Exception as _ex:
            iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
            return False
        org_id = db.query(query="SELECT org_id FROM organizations WHERE name=%s", values=('Фаринелла',),
                          fetch='fetchone')[0]
        customer_id = db.query(query='SELECT guest_id FROM customers WHERE user_id=%s', values=(user_id,),
                               fetch='fetchone')[0]
        params = {
            "id": customer_id,
            "type": "id",
            "organizationId": org_id
        }
        async with ClientSession() as session:
            async with session.post(url=url, headers=token, json=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['surname'] is None:
                        if data['middleName'] is None:
                            name = data['name']
                        else:
                            name = f'{data['name']} {data['middleName']}'
                    else:
                        if data['middleName'] is None:
                            name = f'{data['surname']} {data['name']}'
                        else:
                            name = f'{data['surname']} {data['name']} {data['middleName']}'
                    info = {
                        'name': name,
                        'phone': data['phone'],
                        'email': data['email'],
                        'birthday': data['birthday'],
                        'sex': data['sex'],
                        'cards': data['cards'],
                        'consent_status': data['consentStatus'],
                        'categories': data['categories'],
                        'wallets': data['walletBalances'],
                        'should_receive_promo_actions_info': data['shouldReceivePromoActionsInfo'],
                        'should_receive_royalty_info': data['shouldReceiveLoyaltyInfo'],
                        'should_receive_orderStatus_info': data['shouldReceiveOrderStatusInfo'],
                        'is_deleted': data['isDeleted']
                    }
                    return info
    except Exception as _ex:
        iiko_cloud_api_logger.error(f'Get customer[{user_id}] info error: {_ex}')
        return False


async def check_shift(employee_id):
    url = 'https://api-ru.iiko.services/api/1/employees/shift/is_open'
    try:
        try:
            org_ids = db.query(query="SELECT org_ids FROM employee_couriers WHERE employee_id=%s", fetch='fetchall',
                               values=(employee_id,), log_level=30, debug=True)[0][0]

            org_ids_list = org_ids.replace('{', '').replace('}', '').split(',')

            term_ids_dict = {}
            for org_id in org_ids_list:
                term_id = db.query(query="SELECT terminal_groups FROM organizations WHERE org_id=%s", fetch='fetchall',
                                   values=(org_id,), log_level=30, debug=True)[0][0]
                try:
                    term_id = term_id.replace('{', '').replace('}', '').split(',')
                except:
                    term_id = term_id.replace('{', '').replace('}', '')

                term_ids_dict[org_id] = term_id
            try:
                with open(path_token, 'r', encoding='utf-8') as file:
                    token = json.load(file)
            except Exception as _ex:
                iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
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
            iiko_cloud_api_logger.critical(f'Error fetching data: {_ex}', exc_info=True)
            return False
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error checking shift: {_ex}')
        return False


async def shift_close(user_id):
    url = 'https://api-ru.iiko.services/api/1/employees/shift/clockout'
    emp_id, term_id, org_id = db.query(query="SELECT emp_id, term_open, org_open FROM employee_list WHERE user_id=%s",
                                       fetch='fetchone', values=(user_id,), log_level=30, debug=True)
    params = {
        'organizationId': org_id,
        'terminalGroupId': term_id,
        'employeeId': emp_id
    }
    try:
        with open(path_token, 'r', encoding='utf-8') as file:
            token = json.load(file)
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
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
        iiko_cloud_api_logger.critical(f'Error closing shift for employee <{emp_id}>: {_ex}')
        return False


async def shift_open(user_id, org_id):
    emp_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", values=(user_id,), fetch='fetchone',
                      log_level=30, debug=True)[0]
    term_id = db.query(query="SELECT terminal_groups FROM organizations WHERE org_id=%s", values=(org_id,),
                       fetch='fetchone', log_level=30, debug=True)[0]

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
        iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
        return False
    try:
        async with ClientSession() as session:
            async with session.post(url=url, headers=token, json=params) as resp:
                status = resp.status
                if status == 200:
                    db.query(query='UPDATE employee_list SET term_open=%s, org_open=%s WHERE user_id=%s',
                             values=(term_id_list, org_id, user_id))
                    return True
                else:
                    iiko_cloud_api_logger.error(f'Error opening shift for employee <{emp_id}>: {await resp.json()}')
                    return False
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error opening shift for employee <{emp_id}>: {_ex}')


async def update_stop_list():
    url = 'https://api-ru.iiko.services/api/1/stop_lists'
    org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall', log_level=30, debug=True)
    org_ids_list = []
    for org_id in org_ids:
        org_ids_list.append(org_id[0])
    params = {
        'organizationIds': org_ids_list
    }
    try:
        with open(path_token, 'r', encoding='utf-8') as file:
            token = json.load(file)
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
        return False

    async with ClientSession() as session:
        async with session.post(url=url, headers=token, json=params) as resp:
            status = resp.status
            if status == 200:
                for_check_2 = await check_stop_list()
                try:
                    data = await resp.json()
                    terminalGroup_stoplist = data.get('terminalGroupStopLists')
                    db.query(query="DELETE FROM stop_list")
                    for organization in terminalGroup_stoplist:
                        org_id = organization.get('organizationId')
                        items_1 = organization.get('items')
                        for terminalGroups in items_1:
                            terminalGroup_id = terminalGroups.get('terminalGroupId')
                            items_2 = terminalGroups.get('items')
                            for item in items_2:
                                item_id = item.get('productId')
                                date_add = item.get('dateAdd')
                                balance = item.get('balance')
                                db.query(query="""BEGIN;
                                INSERT INTO stop_list (org_id, item_id, date_add, balance) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
                                UPDATE stop_list SET name = menu.name FROM menu WHERE stop_list.item_id = menu.item_id;
                                DELETE FROM stop_list WHERE stop_list.name IS NULL;""",
                                         values=(org_id, item_id, date_add, balance), log_level=30, debug=True)
                    for_check_1 = await check_stop_list()
                    if for_check_1 != for_check_2:
                        diff = await stop_list_differences(for_check_1, for_check_2)
                        return diff
                    else:
                        return
                except Exception as _ex:
                    iiko_cloud_api_logger.critical(f'Error updating stop list: {_ex}')
                return status
            else:
                iiko_cloud_api_logger.error(f'Error updating stop list: {status}')
                return status


async def update_menu():
    url = 'https://api-ru.iiko.services/api/1/nomenclature'
    try:
        with open(path_token, 'r', encoding='utf-8') as file:
            token = json.load(file)
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error reading token: {_ex}')
        return False
    org_ids = db.query(query="SELECT org_id FROM organizations", fetch='fetchall', log_level=30, debug=True)
    try:
        for org_id in org_ids:
            params = {
                'organizationId': org_id[0]
            }
            async with ClientSession() as session:
                async with session.post(url=url, headers=token, json=params) as resp:
                    status = resp.status
                    if status == 200:
                        data = await resp.json()
                        products = data.get('products')
                        for product in products:
                            if product.get('type') == 'Modifier':
                                continue
                            item_id = product.get('id')
                            name = product.get('name')
                            db.query(
                                query="INSERT INTO menu (org_id, name, item_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                values=(org_id, name, item_id), log_level=30, debug=True)
        return status
    except Exception as _ex:
        iiko_cloud_api_logger.critical(f'Error updating menu: {_ex}')
