import os.path

bot_temp_path = os.path.abspath('./temp/')
bot_logs_path = os.path.abspath('./logs/')
root_path = os.path.abspath('.')

VALIDATION_DIR = os.path.abspath('./.well-known/acme-challenge/')
CERT_PATH = os.path.abspath('./SERVER/cert/fullchain.pem')
KEY_PATH = os.path.abspath('./SERVER/cert/privkey.pem')


print(bot_logs_path, bot_temp_path, root_path, VALIDATION_DIR, CERT_PATH, KEY_PATH)