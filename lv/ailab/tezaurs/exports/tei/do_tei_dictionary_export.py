#!/usr/bin/env python3
from lv.ailab.tezaurs.dbobjects.entries import Entry
from lv.ailab.tezaurs.utils.dict.ili import IliMapping
from lv.ailab.tezaurs.dbaccess.connection import db_connect
from lv.ailab.tezaurs.dbaccess.db_config import db_connection_info
from lv.ailab.tezaurs.dbaccess.overview_querries import get_dict_version, fetch_all_sources
from lv.ailab.tezaurs.exports.tei.tei_output import TEIWriter
from lv.ailab.tezaurs.exports.tei.whitelist import EntryWhitelist
import sys


# Major TODOs:
# - export MWE links
# - homonym grouping
# - migrate to hard sense IDs

connection = None
dbname = None
dict_version = None
whitelist = None

omit_wordparts = False
omit_pot_wordparts = False
omit_mwe = False

do_free_texts = False
do_inflection_texts = False
do_entrylevel_exmples = False


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
dict_version_data = get_dict_version(connection)
dict_version = dict_version_data['tag']
filename = f'{dict_version}_tei{filename_infix}.xml'
with open(filename, 'w', encoding='utf8') as out:
    ili_map = IliMapping()
    tei_printer = TEIWriter(out, dict_version, whitelist)
    tei_printer.print_head(
        dict_version_data['dictionary'], dict_version_data ['title_long'], dict_version_data ['title_short'],
        dict_version_data['release_name_en'], dict_version_data['editors_en'],
        dict_version_data['entries'], dict_version_data['lexemes'], dict_version_data['senses'],
        dict_version_data['year'], dict_version_data['month'],
        dict_version_data['url'], dict_version_data['copyright_en'])
    try:
        for entry in Entry.fetch_all_entries(connection, omit_mwe, omit_wordparts, omit_pot_wordparts, do_entrylevel_exmples):
            tei_printer.print_entry(entry, ili_map)
    except BaseException as err:
        print("Entry was: " + tei_printer.debug_entry_id)
        raise
    tei_printer.print_back_matter(fetch_all_sources(connection))
    tei_printer.print_tail(dict_version_data['dictionary'])
print(f'Done! Output written to {filename}')
