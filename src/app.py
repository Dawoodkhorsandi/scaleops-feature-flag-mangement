from fastapi import FastAPI
from common.settings import get_settings

settings = get_settings()

if __name__ == '__main__':
    print('Running', settings.postgres_dsn)