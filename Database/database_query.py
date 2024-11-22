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



