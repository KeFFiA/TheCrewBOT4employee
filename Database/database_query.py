from .database import db


async def admins_lists():
    developer_id_1 = db.query(query="SELECT user_id FROM users WHERE is_superadmin=true", fetch='fetchall')
    developer_id = [item for tup in developer_id_1 for item in tup]
    admins_list_1 = db.query(query="SELECT user_id FROM users WHERE is_admin=true", fetch='fetchall')
    admins_list = [item for tup in admins_list_1 for item in tup]
    admins_list.extend(developer_id)
    admins_list = [int(d) for d in admins_list]
    return admins_list


async def check_stop_list():
    data = db.query(query="SELECT * FROM stop_list ORDER BY name", fetch='fetchall')
    result = {}

    for org_id, name, item_id, date_add in data:
        org_name = db.query('SELECT name FROM organizations WHERE org_id=%s', values=(org_id,), fetch='fetchone')[0]
        if org_name not in result:
            result[org_name] = {
                "items": []
            }
        result[org_name]["items"].append({
            "name": name,
            "item_id": item_id,
            "date_add": date_add
        })
    return result


async def stop_list_differences(dict_a, dict_b):
    result = {}
    for key, value in dict_a.items():
        result[key] = {'items': []}
        for item in value['items']:
            if key not in dict_b or not any(
                    existing_item['item_id'] == item['item_id'] for existing_item in dict_b[key]['items']):
                result[key]['items'].append(item)
    return result


async def admin_list():
    admins_list_1 = db.query("SELECT user_id FROM users WHERE is_admin=TRUE or is_smm=TRUE", fetch='fetchall')
    admins_list = [item for tup in admins_list_1 for item in tup]
    developer_id_1 = db.query(query="SELECT user_id FROM users WHERE is_superadmin=true", fetch='fetchall')
    developer_id = [item for tup in developer_id_1 for item in tup]
    smm_list_1 = db.query(query="SELECT user_id FROM users WHERE is_smm=true", fetch='fetchall')
    smm_list = [item for tup in smm_list_1 for item in tup]
    users_list = {}

    for ids in admins_list:
        try:
            name, surname = db.query(query="SELECT name, surname FROM customers WHERE user_id=%s",
                                values=(ids,), fetch='fetchone')
            if ids in developer_id:
                pass
            elif ids in admins_list:
                users_list[f'admin_{ids}'] = f'[ADM] {surname} {name}'
                pass
            elif ids in smm_list:
                users_list[f'admin_{ids}'] = f'[SMM] {surname} {name}'
        except:
            pass
    return users_list


