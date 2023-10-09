def extract_gram(element, omit_flags):
    result = {}
    # Legacy POS logic to be substituted with general flag processing
    # if element.paradigm_data and 'Vārdšķira' in element.paradigm_data:
    #    result['pos'] = [element.paradigm_data['Vārdšķira']]
    #    if 'Reziduāļa tips' in element.paradigm_data:
    #        result['pos'].append(element.paradigm_data['Reziduāļa tips'])
    # if element.data and 'Gram' in element.data:
    #    gram = element.data['Gram']
    #    if 'Flags' in gram and 'Kategorija' in gram['Flags'] and gram['Flags']['Kategorija']:
    #        result['pos'] = gram['Flags']['Kategorija']
    #    if 'Flags' in gram and 'Citi' in gram['Flags'] and 'Neviennozīmīga vārdšķira vai kategorija' in \
    #            gram['Flags']['Citi']:
    #        result['pos'] = []
    #    if 'FlagText' in gram and db_connection_info['schema'] != 'tezaurs':
    #        result['pos_text'] = gram['FlagText']
    #    if 'FreeText' in gram and db_connection_info['schema'] != 'tezaurs':
    #        result['pos_text'] = gram['FreeText']

    # General flag/property processing
    if element.data and 'Gram' in element.data and 'Flags' in element.data['Gram'] \
            and element.data['Gram']['Flags']:
        result['flags'] = {}
        result['flags'] = element.data['Gram']['Flags']
    # including flag inheritance from paradigms
    try:
        if element.paradigm_data:
            for key in element.paradigm_data.keys():
                if omit_flags and key in omit_flags:
                    continue
                if 'flags' not in result or not result['flags']:
                    result['flags'] = {}
                if key not in result['flags'] or not result['flags'][key]:
                    result['flags'][key] = element.paradigm_data[key]
    except AttributeError:
        pass

    # Structural restrictions
    if element.data and 'Gram' in element.data and 'StructuralRestrictions' in element.data['Gram'] \
            and element.data['Gram']['StructuralRestrictions']:
        result['struct_restr'] = element.data['Gram']['StructuralRestrictions']

    # Inflection text
    if element.data and 'Gram' in element.data and 'Inflection' in element.data['Gram'] and \
            element.data['Gram']['Inflection']:
        result['infl_text'] = element.data['Gram']['Inflection']

    # Free text
    if element.data and 'Gram' in element.data and 'FreeText' in element.data['Gram'] and \
            element.data['Gram']['FreeText']:
        result['free_text'] = element.data['Gram']['FreeText']

    # Paradigms
    if hasattr(element, 'paradigm') and element.paradigm:
        result['paradigm'] = extract_paradigm_stems(element)

    return result


def extract_paradigm_stems(element):
    result = {}
    if hasattr(element, 'paradigm') and element.paradigm:
        result = {'id': element.paradigm}
        if hasattr(element, 'stem1') and element.stem1:
            result['stem_inf'] = element.stem1
        if hasattr(element, 'stem2') and element.stem2:
            result['stem_pres'] = element.stem2
        if hasattr(element, 'stem3') and element.stem3:
            result['stem_past'] = element.stem3
    return result


def lmfiy_pos(pos, abbr_type, lemma):
    if not pos:
        return 'u'
    elif pos == 'Lietvārds' \
            or pos == 'Saīsinājums' and (abbr_type == 'Sugasvārds' or abbr_type == 'Īpašvārds'):
        return 'n'
    elif pos == 'Darbības vārds' or pos == 'Divdabis' \
            or pos == 'Saīsinājums' and abbr_type == 'Verbāls':
        return 'v'
    elif pos == 'Īpašības vārds' \
            or pos == 'Saīsinājums' and abbr_type == 'Īpašības vārds':
        return 'a'
    elif pos == 'Apstākļa vārds' \
            or pos == 'Saīsinājums' and abbr_type == 'Apstāklis':
        return 'r'
    elif pos == 'Prievārds':
        return 'p'
    elif pos == 'Partikula' or pos == 'Saiklis' or pos == 'Izsauksmes vārds' \
            or pos == 'Vietniekvārds' or pos == 'Skaitļa vārds':
        return 'x'
    elif pos == 'Reziduālis':
        return 'u'
    else:
        print(f'Unknown POS {pos} for lemma {lemma}.')
        return 'u'


def extract_paradigm_text(paradigm_data):
    paradigm_text = paradigm_data['id']

    if 'stem_inf' in paradigm_data or 'stem_pres' in paradigm_data \
            or 'stem_past' in paradigm_data:
        paradigm_text = paradigm_text + ':'
        if 'stem_inf' in paradigm_data:
            paradigm_text = paradigm_text + paradigm_data['stem_inf'] + ';'
        else:
            paradigm_text = paradigm_text + ';'
        if 'stem_pres' in paradigm_data:
            paradigm_text = paradigm_text + paradigm_data['stem_pres'] + ';'
        else:
            paradigm_text = paradigm_text + ';'
        if 'stem_past' in paradigm_data:
            paradigm_text = paradigm_text + paradigm_data['stem_past']
    return paradigm_text
