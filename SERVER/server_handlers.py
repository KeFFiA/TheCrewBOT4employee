
from API_SCRIPTS.iiko_cloudAPI import update_stop_list
from Bot.Utils.logging_settings import server_logger
from Database.database_query import check_stop_list


async def stop_list_server():
    try:
        diff_list = await update_stop_list()
        new_items_text = ''
        try:
            for k, items in diff_list.items():
                if len(items.get('items')) == 0:
                    continue
                item = items.get('items')[0]
                name = item.get('name')
                new_items_text += f'<b>{k}</b> - {name}\n'
        except:
            return 'Break', 'Break'
        already_stop_list = await check_stop_list()
        already_stop_text = ''
        for k, items in already_stop_list.items():
            already_stop_text += f'<b>{k}</b>\n\n'
            for item in items.get('items'):
                name = item.get('name')
                already_stop_text += f'<b>{name}</b>\n'
            already_stop_text += '\n'
        if len(new_items_text) > 0:
            return new_items_text, already_stop_text
        else:
            return 'Break', 'Break'
    except Exception as _ex:
        server_logger.error(f'Exception occurred: {_ex}')
        return 'Break', 'Break'


