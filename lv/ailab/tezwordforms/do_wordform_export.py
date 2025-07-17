#!/usr/bin/env python3
import json

from lv.ailab.tezwordforms.wordform_utils import LexemeProperties, WordformReader
import sys
import warnings

warn_multiple_influrls = True
warn_multiple_inflsets = True

do_ispell = True
do_tei = False
lexeme_properties_path = "influrl-to-lexdata.json"
wordform_list_path = "inflection-export.json"
dict_version = "tezaurs_00_0"

if len(sys.argv) > 1:
    dict_version = sys.argv[1]
if len(sys.argv) > 2:
    wordform_list_path = sys.argv[2]
if len(sys.argv) > 3:
    lexeme_properties_path = sys.argv[3]

lexeme_properties = LexemeProperties(lexeme_properties_path)
wordform_source = WordformReader(wordform_list_path)

ispell_forms = {}

for infl_json in wordform_source.process_line_by_line():
    if not infl_json or len(infl_json) < 1:
        continue
    if warn_multiple_influrls and len(infl_json) != 1:
        warnings.warn("Following wordform JSON doesn't have exactly one key: " + json.dumps(infl_json, ensure_ascii=False))
    infl_url = next(iter(infl_json))
    if do_tei or do_ispell and lexeme_properties.lexeme_good_for_spelling(infl_url):
        if warn_multiple_inflsets and len(infl_json[infl_url]) != 1:
            warnings.warn("Following wordform JSON doesn't have exactly one set of inflections: " + json.dumps(infl_json, ensure_ascii=False))
        infl_set = next(iter(infl_json[infl_url]))
        for form in infl_set:
            if do_ispell and lexeme_properties.form_good_for_spelling(form):
                try:
                    ispell_forms[form["Vārds"]] = 1
                except KeyError as e:
                    warnings.warn(f'Missing key "Vārds" for {infl_url} in {json.dumps(form, ensure_ascii=False)}')
                    continue

if do_ispell:
    ispell_filename = f'{dict_version}.ispell'
    ispell_output = open(ispell_filename, 'w', encoding='utf8')
    sorted_forms = sorted(ispell_forms.keys(), key=lambda x: x.lower())
    for form in sorted_forms:
        ispell_output.writelines(f'{form}\n')
    ispell_output.close()
