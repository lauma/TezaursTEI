#!/usr/bin/env python3
from lv.ailab.tezdb.connection import db_connect
from lv.ailab.tezdb.db_config import db_connection_info
from lv.ailab.tezdb.overview_querries import get_dict_version, fetch_all_paradigms
from lv.ailab.tezdb.query_uttils import combine_inhereted_flags
from lv.ailab.teztei.tei_output import TEIWriter
from lv.ailab.tezwordforms.wordform_utils import WordformReader, LexemeProperties
import json
import sys
import warnings

warn_multiple_influrls = True
warn_multiple_inflsets = False

# DB connection is only needed for general dictionary info and paradigm flags, all the rest comes from JSON files.
connection = None
dbname = None
dict_version = None
paradigms = None
lexeme_properties_path = "influrl-to-lexdata.json"
wordform_list_path = "inflection-export.json"

if len(sys.argv) > 1:
    dbname = sys.argv[1]
if dbname:
    db_connection_info['dbname'] = dbname
else:
    dbname = db_connection_info['dbname']

if len(sys.argv) > 2:
    wordform_list_path = sys.argv[2]
wordform_source = WordformReader(wordform_list_path, True)

if len(sys.argv) > 3:
    lexeme_properties_path = sys.argv[3]
lexeme_properties = LexemeProperties(lexeme_properties_path)

connection = db_connect()
dict_version_data = get_dict_version(connection)
dict_version = dict_version_data['tag']
paradigms = fetch_all_paradigms(connection)
filename = f'{dict_version}_wordforms_tei.xml'
with open(filename, 'w', encoding='utf8') as out:
    tei_printer = TEIWriter(out, dict_version, None, ' ')
    tei_printer.print_head(
        f"{dict_version_data['dictionary']}_wordforms", dict_version_data['title_long'], dict_version_data['title_short'],
        dict_version_data['release_name_en'], dict_version_data['editors_en'],
        dict_version_data['entries'], dict_version_data['lexemes'], dict_version_data['senses'],
        dict_version_data['year'], dict_version_data['month'],
        dict_version_data['url'], dict_version_data['copyright_en'])

    for infl_json in wordform_source.process_line_by_line():
        if not infl_json or len(infl_json) < 1:
            continue
        if warn_multiple_influrls and len(infl_json) != 1:
            warnings.warn(
                "Following wordform JSON doesn't have exactly one key: " \
                    + json.dumps(infl_json, ensure_ascii=False))
        infl_url = next(iter(infl_json))
        if warn_multiple_inflsets and len(infl_json[infl_url]) != 1:
            warnings.warn(
                "Following wordform JSON doesn't have exactly one set of inflections: " \
                    + json.dumps(infl_json, ensure_ascii=False))
        infl_set = next(iter(infl_json[infl_url]))
        property_sets = lexeme_properties.property_map[infl_url]
        if not property_sets:
            warnings.warn(f"URI {infl_url} has no lexeme property object, excluded from TEI result.")
        else:
            for properties in property_sets:
                lexeme_flags = {}
                if 'flags' in properties:
                    lexeme_flags = properties['flags']
                flags = combine_inhereted_flags(lexeme_flags, paradigms[properties['paradigm']],
                                                {'Stems', 'Morfotabulas tips', 'Paradigmas īpatnības'})
                tei_printer.print_wordform_set_entry(
                    properties['entry_id'], properties['lexeme_id'], properties['lemma'], flags, infl_set)

    tei_printer.print_tail(f"{dict_version_data['dictionary']}_wordforms")

print(f'Done! Output written to {filename}')
wordform_source.print_bad_line_log()
