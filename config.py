import os


def env(NAME: str):
    result = os.getenv(NAME)
    if not result:
        raise KeyError(f'Не задана переменная окружения: "{NAME}"')
    return result

def _get_testing():
    env = os.getenv("TESTING")
    if env is None:
        return False
    match env.lower():
        case "true":
            return True
        case "false":
            return False
        case _:
            raise ValueError(f'TESTING: Неизвестный ключ "{env}"')

TESTING = _get_testing()
TOKEN = env('TOKEN')
PAYMENTS_TOKEN = env('PAYMENTS_TOKEN')
ADMINS_NAME = [env('ADMIN_NAME')]
