from lv.ailab.tezdb.db_config import db_connection_info

import psycopg2


def db_connect():
    if db_connection_info is None or db_connection_info["host"] is None or len(db_connection_info["host"]) == 0:
        print("Postgres connection error: connection information must be supplied in db_config")
        raise Exception("Postgres connection error: connection information must be supplied in <conn_info>")

    print(f'Connecting to database {db_connection_info["dbname"]}, schema {db_connection_info["schema"]}')
    connection = psycopg2.connect(
            host=db_connection_info['host'],
            port=db_connection_info['port'],
            dbname=db_connection_info['dbname'],
            user=db_connection_info['user'],
            password=db_connection_info['password'],
            options=f'-c search_path={db_connection_info["schema"]}',
        )
    return connection
