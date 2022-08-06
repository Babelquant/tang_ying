from sqlalchemy import create_engine
from tangying import settings

def initSqliteEngine():
    global sqlite_engine
    database_name = settings.DATABASES['default']['NAME']
    database_url = 'sqlite:///{database_name}'.format(database_name=database_name)
    sqlite_engine = create_engine(database_url,echo=False)

def getSqliteEngine():
    return sqlite_engine