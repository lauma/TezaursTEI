#!/usr/bin/env python3
from lv.ailab.teztei.db_config import db_connection_info
from lv.ailab.teztei.querries import fetch_entries
from lv.ailab.teztei.tei_output import TEI_Writer
from lv.ailab.teztei.whitelist import EntryWhitelist

import psycopg2
import sys

# Major TODOs:
# - entry grammars
# - export MWE links
# - homonym grouping
# - migrate to hard sense IDs

connection = None
dbname = None
whitelist = None

omit_wordparts = False
omit_pot_wordparts = False
omit_mwe = False

do_free_texts = False
do_inflection_texts = False

def db_connect():
    global connection
    global dbname

    if db_connection_info is None or db_connection_info["host"] is None or len(db_connection_info["host"]) == 0:
        print("Postgres connection error: connection information must be supplied in db_config")
        raise Exception("Postgres connection error: connection information must be supplied in <conn_info>")

    if dbname:
        db_connection_info['dbname'] = dbname
    else:
        dbname = db_connection_info['dbname']
    print(f'Connecting to database {db_connection_info["dbname"]}, schema {db_connection_info["schema"]}')
    connection = psycopg2.connect(
            host=db_connection_info['host'],
            port=db_connection_info['port'],
            dbname=db_connection_info['dbname'],
            user=db_connection_info['user'],
            password=db_connection_info['password'],
            options=f'-c search_path={db_connection_info["schema"]}',
        )


if len(sys.argv) > 1:
    dbname = sys.argv[1]
if len(sys.argv) > 2:
    whitelist = EntryWhitelist()
    whitelist.load(sys.argv[2])
    if len(whitelist.entries) < 1:
        whitelist = None
filename_infix = ""
if whitelist is not None:
    filename_infix = "_filtered"
db_connect()
filename = f'{db_connection_info["dbname"]}_tei{filename_infix}.xml'
with open(filename, 'w', encoding='utf8') as f:
    tei_printer = TEI_Writer(f, dbname, whitelist)
    tei_printer.print_head()
    for entry in fetch_entries(connection, omit_mwe, omit_wordparts, omit_pot_wordparts):
        tei_printer.print_entry(entry)
    tei_printer.print_tail()
print(f'Done! Output written to {filename}')
