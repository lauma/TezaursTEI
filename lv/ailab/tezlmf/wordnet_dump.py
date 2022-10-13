#!/usr/bin/env python3
from lv.ailab.tezdb.connection import db_connect
from lv.ailab.tezdb.db_config import db_connection_info

import sys

connection = None
dbname = None

if len(sys.argv) > 1:
    dbname = sys.argv[1]
if dbname:
    db_connection_info['dbname'] = dbname
else:
    dbname = db_connection_info['dbname']

connection = db_connect()
filename = f'{db_connection_info["dbname"]}_lmf.xml'
with open(filename, 'w', encoding='utf8') as f:
    #TODO
print(f'Done! Output written to {filename}')
