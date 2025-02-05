#!/usr/bin/env python3
from lv.ailab.tezdb.connection import db_connect
from lv.ailab.tezdb.db_config import db_connection_info

import sys

from lv.ailab.tezdb.overview_querries import fetch_all_synsets, fetch_all_synseted_lexemes, get_dict_version
from lv.ailab.tezdb.single_sinset_queries import fetch_synset_senses, fetch_synset_lexemes, fetch_synset_relations, \
    fetch_exteral_synset_eq_relations
from lv.ailab.tezdb.subentry_queries import fetch_synseted_senses_by_lexeme
from lv.ailab.dictutils.ili import IliMapping
from lv.ailab.tezlmf.lmf_output import LMFWriter

# TODO: izrunas, LMF POS no tēzaura vārdšķiras
wordnet_id = 'wordnet_lv'
wordnet_vers = '1.0'
connection = None
dbname = None
dict_version = None
print_tags = True

if len(sys.argv) > 1:
    dbname = sys.argv[1]
if dbname:
    db_connection_info['dbname'] = dbname
else:
    dbname = db_connection_info['dbname']

ili = IliMapping()
connection = db_connect()
dict_version_data = get_dict_version(connection)
dict_version = dict_version_data['tag']
filename = f'{dict_version}_lmf.xml'
with open(filename, 'w', encoding='utf8') as f:
    lmf_printer = LMFWriter(f, dict_version, wordnet_id)
    lmf_printer.print_head(wordnet_vers)
    try:
        for lexeme in fetch_all_synseted_lexemes(connection):
            synset_senses = fetch_synseted_senses_by_lexeme(connection, lexeme['id'])
            lmf_printer.print_lexeme(lexeme, synset_senses, print_tags)
    except BaseException as err:
        print("Lexeme was: " + lmf_printer.debug_id)
        raise
    try:
        for synset_id in fetch_all_synsets(connection):
            synset_senses = fetch_synset_senses(connection, synset_id)
            synset_lexemes = fetch_synset_lexemes(connection, synset_id)
            relations = fetch_synset_relations(connection, synset_id)
            omw_relations = fetch_exteral_synset_eq_relations(connection, synset_id, 'pwn-3.0')
            # Drukās netukšos sinsetus, šobrīd tas nozīmē, ka vajag definīciju un leksēmu.
            if synset_senses and synset_lexemes:
                lmf_printer.print_synset(synset_id, synset_senses, synset_lexemes, relations, omw_relations, ili)
    except BaseException as err:
        print("Synset was: " + lmf_printer.debug_id)
        raise
    lmf_printer.print_tail()
print(f'Done! Output written to {filename}')
