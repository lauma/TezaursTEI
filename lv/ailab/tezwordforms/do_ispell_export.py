#!/usr/bin/env python3
from lv.ailab.tezwordforms.wordform_utils import IspellFilter, WordformReader
import json
import sys
import warnings

warn_multiple_inflsets = True
skip_multiple_inflsets = True
# Šobrīd vairāki locījumu komplekti ir tikai gadījumos, kad saīsinājumu kļūdaini sadala divās
# tekstvienībās, tāpēc labāk ir tos visus izlaist. Šis jāmaina, kad salabos saīsinājumus.

wordform_list_path = "inflections.jsonl"
dict_version = "tezaurs_00_0"

if len(sys.argv) > 1:
    dict_version = sys.argv[1]
if len(sys.argv) > 2:
    wordform_list_path = sys.argv[2]

wordform_source = WordformReader(wordform_list_path)
ispell_filter = IspellFilter()
ispell_forms = {}

for infl_json in wordform_source.process_line_by_line():
    if not infl_json or len(infl_json) < 1:
        continue

    if ispell_filter.lexeme_good_for_spelling(infl_json):
        if warn_multiple_inflsets and len(infl_json['inflectedForms']) != 1:
            warnings.warn("Following wordform JSON doesn't have exactly one set of inflections: " + json.dumps(infl_json, ensure_ascii=False))
        if skip_multiple_inflsets and len(infl_json['inflectedForms']) != 1:
            continue
        for infl_set in infl_json['inflectedForms']:
            for form in infl_set:
                if ispell_filter.form_good_for_spelling(form):
                    try:
                        ispell_forms[form["Vārds"]] = 1
                    except KeyError as e:
                        warnings.warn(f'Missing key "Vārds" in {json.dumps(form, ensure_ascii=False)}')
                        try:
                            ispell_forms[form["V\uFFFD\uFFFDrds"]] = 1
                            print ('FFFD workaround for ispell successfull')
                        except KeyError:
                            continue
                        continue

ispell_filename = f'{dict_version}.ispell'
ispell_output = open(ispell_filename, 'w', encoding='utf8')
sorted_forms = sorted(ispell_forms.keys(), key=lambda x: x.lower())
for form in sorted_forms:
    ispell_output.write(f'{form}\n')
ispell_output.close()

wordform_source.print_bad_line_log()
