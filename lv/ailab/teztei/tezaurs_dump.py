#!/usr/bin/env python3
from lv.ailab.tezdb.connection import db_connect
from lv.ailab.tezdb.db_config import db_connection_info
from lv.ailab.teztei.querries import fetch_entries
from lv.ailab.teztei.tei_output import TEIWriter
from lv.ailab.teztei.whitelist import EntryWhitelist

import sys

# Major TODOs:
# - export MWE links
# - homonym grouping
# - examples and example grammar
# - migrate to hard sense IDs

connection = None
dbname = None
whitelist = None

omit_wordparts = False
omit_pot_wordparts = False
omit_mwe = False

do_free_texts = False
do_inflection_texts = False


if len(sys.argv) > 1:
    dbname = sys.argv[1]
if dbname:
    db_connection_info['dbname'] = dbname
else:
    dbname = db_connection_info['dbname']

if len(sys.argv) > 2:
    whitelist = EntryWhitelist()
    whitelist.load(sys.argv[2])
    if len(whitelist.entries) < 1:
        whitelist = None
filename_infix = ""
if whitelist is not None:
    filename_infix = "_filtered"

connection = db_connect()
filename = f'{db_connection_info["dbname"]}_tei{filename_infix}.xml'
with open(filename, 'w', encoding='utf8') as f:
    tei_printer = TEIWriter(f, dbname, whitelist)
    tei_printer.print_head()
    try:
        for entry in fetch_entries(connection, omit_mwe, omit_wordparts, omit_pot_wordparts):
            tei_printer.print_entry(entry)
    except BaseException as err:
        print("Entry was: " + tei_printer.debug_entry_id)
        raise
    tei_printer.print_tail()
print(f'Done! Output written to {filename}')
