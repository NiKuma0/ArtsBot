import os


def env(NAME: str):
    result = os.getenv(NAME)
    if not result:
        raise ValueError(f'Не задана переменная окружения: "{NAME}"')
    return result


TESTING = True
TOKEN = env('TOKEN')
ADMINS_NAME = [env('ADMIN_NAME')]
