#!/usr/bin/env python3
from lv.ailab.tezdb.connection import db_connect
from lv.ailab.tezdb.db_config import db_connection_info

import sys

from lv.ailab.tezdb.overview_querries import fetch_synsets, fetch_synseted_lexemes
from lv.ailab.tezdb.single_sinset_queries import fetch_synset_senses, fetch_synset_lexemes, fetch_synset_relations
from lv.ailab.tezlmf.lmf_output import LMFWriter

# TODO: izrunas, LMF POS no tēzaura vārdšķiras
wordnet_id = 'wordnet_lv'
wordnet_vers = '1.0'
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
    lmf_printer = LMFWriter(f, dbname, wordnet_id)
    lmf_printer.print_head(wordnet_vers)
    try:
        for lexeme in fetch_synseted_lexemes(connection):
            lmf_printer.print_lexeme(lexeme)
    except BaseException as err:
        print("Lexeme was: " + lmf_printer.debug_id)
        raise
    try:
        for synset_id in fetch_synsets(connection):
            synset_senses = fetch_synset_senses(connection, synset_id)
            synset_lexemes = fetch_synset_lexemes(connection, synset_id)
            relations = fetch_synset_relations(connection, synset_id)
            if synset_senses and synset_lexemes and relations:
                lmf_printer.print_synset(synset_id, synset_senses, synset_lexemes, relations)
    except BaseException as err:
        print("Synset was: " + lmf_printer.debug_id)
        raise
    lmf_printer.print_tail()
print(f'Done! Output written to {filename}')
