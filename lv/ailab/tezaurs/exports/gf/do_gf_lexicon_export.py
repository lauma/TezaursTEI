#!/usr/bin/env python3
from lv.ailab.tezaurs.dbaccess.connection import db_connect
from lv.ailab.tezaurs.dbaccess.db_config import db_connection_info
from lv.ailab.tezaurs.dbaccess.overview_querries import get_dict_version, fetch_all_lexemes_with_paradigms
import sys

from lv.ailab.tezaurs.exports.gf.gf_output import GFConcreteWriter, GFAbstractWriter

connection = None
dbname = None
dict_version = None
implemented_paradigms = {
            "noun-1a", "noun-1b", "noun-2a", "noun-2b", "noun-2c", "noun-2d",
			"noun-3f", "noun-3m", "noun-4f", "noun-4m", "noun-5fa", "noun-5fb",
			"noun-5ma", "noun-5mb", "noun-6a", "noun-6b",
}

if len(sys.argv) > 1:
    dbname = sys.argv[1]
if dbname:
    db_connection_info['dbname'] = dbname
else:
    dbname = db_connection_info['dbname']

connection = db_connect()
dict_version_data = get_dict_version(connection)
dict_version = dict_version_data['tag']
dict_lang = 'Ltg' if dict_version_data['dictionary'] == 'ltg' else 'Lav'

module_name_abs = f'PortedTezaursDict{dict_lang}Abs'
gf_abs_printer = GFAbstractWriter(f'{module_name_abs}.gf')
gf_abs_printer.print_head(module_name_abs, dict_version)

module_name_conc = f'PortedTezaursDict{dict_lang}'
gf_conc_printer = GFConcreteWriter(f'{module_name_conc}.gf')
gf_conc_printer.print_head(module_name_conc, module_name_abs, dict_version)

for lexeme in fetch_all_lexemes_with_paradigms(connection):
    gfPos = None
    if lexeme['paradigm'] not in implemented_paradigms:
        continue
    if lexeme['changed_pos']:
        print(f'Skipping {lexeme["lemma"]} because of pos!')
        continue
    else:
        gfPos = 'N' # TODO other POS

    gf_abs_printer.print_lexeme(lexeme['lemma'], gfPos, lexeme['paradigm'])

    if 'irregular_lemma' not in lexeme or len(lexeme['irregular_lemma']) < 1:
        gf_conc_printer.print_normal_lexeme(lexeme['lemma'], lexeme['paradigm'])
    elif len(lexeme['irregular_lemma']) == 1 and 'Daudzskaitlis' in lexeme['irregular_lemma']:
        gf_conc_printer.print_plural_lexeme(lexeme['lemma'], lexeme['paradigm'])

    #TODO: papildformas un aizstājošās formas
    #TODO: sinsetu ID


gf_abs_printer.print_tail()
gf_conc_printer.print_tail()

