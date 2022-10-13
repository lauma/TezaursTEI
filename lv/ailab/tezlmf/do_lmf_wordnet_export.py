#!/usr/bin/env python3
from lv.ailab.tezdb.connection import db_connect
from lv.ailab.tezdb.db_config import db_connection_info

import sys

from lv.ailab.tezlmf.lmf_output import LMFWriter

wordnet_vers = "1.0"

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
    lmf_printer = LMFWriter(f, dbname)
    lmf_printer.print_head(wordnet_vers)
    # TODO
    lmf_printer.print_tail()
print(f'Done! Output written to {filename}')
