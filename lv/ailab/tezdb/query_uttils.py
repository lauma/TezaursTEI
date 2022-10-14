def extract_gram(element):
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
    if hasattr(element, 'paradigm_data') and element.paradigm_data:
        for key in element.paradigm_data.keys():
            if not element.paradigm_data[key]:
                result['flags'][key] = element.paradigm_data[key]

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
        result['paradigm'] = {'id': element.paradigm}
        if hasattr(element, 'stem1') and element.stem1:
            result['paradigm']['stem_inf'] = element.stem1
        if hasattr(element, 'stem2') and element.stem2:
            result['paradigm']['stem_pres'] = element.stem2
        if hasattr(element, 'stem3') and element.stem3:
            result['paradigm']['stem_past'] = element.stem3

    return result


def lmfiy_pos(pos, lemma):
    if not pos:
        return 'u'
    elif pos == 'Lietvārds':
        return 'n'
    elif pos == 'Darbības vārds' or pos == 'Divdabis':
        return 'v'
    elif pos == 'Īpašības vārds':
        return 'a'
    elif pos == 'Apstākļa vārds':
        return 'r'
    elif pos == 'Prievārds':
        return 'p'

    else:
        print(f'Unknown POS {pos} for lemma {lemma}.')
        return 'x'
