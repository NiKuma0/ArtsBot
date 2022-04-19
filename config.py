import os


TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise 'Создайте файл .env'
ADMINS_NAME = os.getenv('ADMINS_NAME')
