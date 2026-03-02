#!/usr/bin/env python3
from lv.ailab.tezaurs.dbaccess.connection import db_connect
from lv.ailab.tezaurs.dbaccess.db_config import db_connection_info
from lv.ailab.tezaurs.dbaccess.overview_querries import get_dict_version, fetch_all_lexemes_with_paradigms_and_synsets
import sys

from lv.ailab.tezaurs.exports.gf.gf_output import GFConcreteWriter, GFAbstractWriter
from lv.ailab.tezaurs.exports.gf.gf_utils import GFUtils
from lv.ailab.tezaurs.utils.dict.db_wordform_utils import filter_wordforms

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

result_lexemes_by_concrete = {}

# Currently only noun processing. Must be updated for other POS, when structure becomes clearer.
for lexeme in fetch_all_lexemes_with_paradigms_and_synsets(connection):
    gf_pos = None
    if lexeme['paradigm'] not in implemented_paradigms:
        continue
    if lexeme['changed_pos']:
        print(f'Skipping {lexeme["lemma"]} because of pos!')
        continue
    else:
        gf_pos = 'N'
        # TODO other POS, use LP and one for place names
    # TODO better treatment for plurale tantum

    conc_expr = None

    lemma_irregs = []\
        if 'combined_flags' not in lexeme or 'Leksēmas pamatformas īpatnības' not in lexeme['combined_flags']\
        else lexeme['combined_flags']['Leksēmas pamatformas īpatnības']
    if len(lemma_irregs) < 1:
        conc_expr = GFUtils.form_concrete_lex_expr('Lemma', lexeme['lemma'], lexeme['paradigm'])
    elif len(lemma_irregs) == 1 and 'Vienskaitlis' in lemma_irregs:
        # Currently singular only nouns do not have special treatment,
        # but if need be, this is the place to do it.
        conc_expr = GFUtils.form_concrete_lex_expr('Lemma', lexeme['lemma'], lexeme['paradigm'])
    elif len(lemma_irregs) == 1 and 'Daudzskaitlis' in lemma_irregs:
        conc_expr = GFUtils.form_concrete_lex_expr('NomPl', lexeme['lemma'], lexeme['paradigm'])
    else:
        print(f'Skipping {lexeme["lemma"]} because of lemma type {lemma_irregs}!')
        continue

    # TODO Cēsīm nav vienskaitļa

    if 'wordforms' in lexeme and lexeme['wordforms'] and len(lexeme['wordforms']) > 0:
        sg_voc_wfs, leftover_wordforms = filter_wordforms(
            lexeme['wordforms'], {"Skaitlis": "Vienskaitlis", "Locījums": "Vokatīvs"})
        pl_voc_wfs, leftover_wordforms = filter_wordforms(
            leftover_wordforms, {"Skaitlis": "Daudzskaitlis", "Locījums": "Vokatīvs"})

        extended_gf_table = GFUtils.form_table_with_vocative_extension(sg_voc_wfs, pl_voc_wfs)

        if not extended_gf_table or leftover_wordforms and len(leftover_wordforms) > 0:
            print(f'Skipping {lexeme["lemma"]} because additional wordforms are not all vocatives!')
            continue
        # Here we form something like this:
        # let bro = noun_2a_fromLemma "brālis" in {
        #   s = table { Sg => bro.s ! Sg ** variants{ "brāl" ; bro.s ! Sg ! Voc } ;
        #     Pl => bro.s ! Pl ** { Voc => "brāļi" } } ;
        #   gend = bro.gend } ;
        conc_expr = f"let {GFUtils.DEFAULT_LET_VARIABLE} = {conc_expr} in {{ s = {extended_gf_table} ; gend = {GFUtils.DEFAULT_LET_VARIABLE}.gend }}"

    if conc_expr:
        result_entry = result_lexemes_by_concrete[(conc_expr, gf_pos)]\
            if (conc_expr, gf_pos) in result_lexemes_by_concrete\
            else {'lemmas': set(), 'ids': set(), 'synsets': set()}
        result_entry['lemmas'].add(lexeme['lemma'])
        result_entry['ids'].add(lexeme['id'])
        result_entry['synsets'].update(lexeme['external_synsets'])
        result_lexemes_by_concrete[(conc_expr, gf_pos)] = result_entry

for (conc_expr, gf_pos) in result_lexemes_by_concrete.keys():
    gf_lexeme_data = result_lexemes_by_concrete[(conc_expr, gf_pos)]
    variable_postfix = GFUtils.BIG_SEPARATOR.join(str(id) for id in sorted(gf_lexeme_data['ids']))
    variable_postfix = f"{variable_postfix}{GFUtils.BIG_SEPARATOR}{gf_pos}"
    synset_comment = GFUtils.form_synest_comment(gf_lexeme_data['synsets'])
    if len(gf_lexeme_data['lemmas']) > 1:
        print(f"Warning: from lemma set {{ {'; '.join(gf_lexeme_data['lemmas'])} }} picking \"{gf_lexeme_data['lemmas'][0]}\"!\n")
    #if len(gf_lexeme_data['gf_pos']) > 1:
    #    print(f"Warning: for {gf_lexeme_data['lemmas'][0]} from POS set {{ {'; '.join(gf_lexeme_data['gf_pos'])} }} picking \"{gf_lexeme_data['gf_pos'][0]}\"!\n")

    gf_abs_printer.print_lexeme(list(gf_lexeme_data['lemmas'])[0], variable_postfix, gf_pos, synset_comment)
    gf_conc_printer.print_lexeme(list(gf_lexeme_data['lemmas'])[0], variable_postfix, conc_expr, synset_comment)

gf_abs_printer.print_tail()
gf_conc_printer.print_tail()
