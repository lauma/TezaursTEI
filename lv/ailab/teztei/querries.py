from psycopg2.extras import NamedTupleCursor

from lv.ailab.teztei.db_config import db_connection_info

# TODO paprasīt P un sataisīt smukāk kveriju veidošanu.


def query(sql, parameters, connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    cursor.execute(sql, parameters)
    r = cursor.fetchall()
    cursor.close()
    return r


def fetch_entries(connection, omit_mwe=False, omit_wordparts=False, omit_pot_wordparts=False):
    entry_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    where_clause = ""
    if omit_mwe or omit_wordparts:
        where_clause = """et.name = 'word'"""
        if not omit_wordparts:
            where_clause = where_clause + """ or et.name = 'wordPart'"""
        if not omit_mwe:
            where_clause = where_clause + """ or et.name = 'mwe'"""
        where_clause = '(' + where_clause + ')' + " and"
    sql_entries = f"""
SELECT e.id, type_id, name as type_name, heading, human_key, homonym_no, primary_lexeme_id, e.data->>'Etymology' as etym
FROM {db_connection_info['schema']}.entries e
JOIN {db_connection_info['schema']}.entry_types et ON e.type_id = et.id
WHERE {where_clause} NOT e.hidden
ORDER BY human_key
"""
    entry_cursor.execute(sql_entries)
    counter = 0
    while True:
        rows = entry_cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            counter = counter + 1
            result = {'id': row.human_key, 'hom_id': row.homonym_no, 'type': row.type_name, 'headword': row.heading}
            if row.etym:
                result['etym'] = row.etym
            lexemes = fetch_lexemes(connection, row.id, row.primary_lexeme_id)
            if lexemes:
                result['lexemes'] = lexemes
            # primary_lexeme = fetch_main_lexeme(connection, row.primary_lexeme_id, row.human_key)
            primary_lexeme = lexemes[0]
            if not primary_lexeme:
                continue
            if omit_pot_wordparts and \
                    (row.type_name == 'wordPart' or primary_lexeme['lemma'].startswith('-') or
                     primary_lexeme['lemma'].endswith('-')):
                continue
            #prim_lex = {'lemma': primary_lexeme.lemma}
            # result['mainLexeme'] = prim_lex
            senses = fetch_senses(connection, row.id)
            if senses:
                result['senses'] = senses
            yield result
        print(f'{counter}\r')


def fetch_lexemes(connection, entry_id, main_lex_id):
    if not entry_id:
        return
    lexeme_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_senses = f"""
SELECT l.id, lemma, lt.name as lexeme_type, p.human_key as paradigm, stem1, stem2, stem3, l.data, p.data as paradigm_data 
FROM {db_connection_info['schema']}.lexemes l
JOIN {db_connection_info['schema']}.lexeme_types lt ON l.type_id = lt.id
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE entry_id = {entry_id} and NOT hidden
ORDER BY (l.id!={main_lex_id}), order_no
"""
    lexeme_cursor.execute(sql_senses)
    lexemes = lexeme_cursor.fetchall()
    if not lexemes:
        return
    result = []
    for lexeme in lexemes:
        lexeme_dict = {'lemma': lexeme.lemma}

        # Legacy POS logic to be substituted with general flag processing
        if lexeme.paradigm_data and 'Vārdšķira' in lexeme.paradigm_data:
            lexeme_dict['pos'] = [lexeme.paradigm_data['Vārdšķira']]
            if 'Reziduāļa tips' in lexeme.paradigm_data:
                lexeme_dict['pos'].append(lexeme.paradigm_data['Reziduāļa tips'])
        if lexeme.data and 'Gram' in lexeme.data:
            gram = lexeme.data['Gram']
            if 'Flags' in gram and 'Kategorija' in gram['Flags'] and gram['Flags']['Kategorija']:
                lexeme_dict['pos'] = gram['Flags']['Kategorija']
            if 'Flags' in gram and 'Citi' in gram['Flags'] and 'Neviennozīmīga vārdšķira vai kategorija' in \
                    gram['Flags']['Citi']:
                lexeme_dict['pos'] = []
            if 'FlagText' in gram and db_connection_info['schema'] != 'tezaurs':
                lexeme_dict['pos_text'] = gram['FlagText']
            if 'FreeText' in gram and db_connection_info['schema'] != 'tezaurs':
                lexeme_dict['pos_text'] = gram['FreeText']

        # General flag/property processing
        lexeme_dict['type'] = lexeme.lexeme_type
        if lexeme.data and 'Pronunciations' in lexeme.data:
            lexeme_dict['pronun'] = lexeme.data['Pronunciations']
        lexeme_dict['flags'] = {}
        if lexeme.data and 'Gram' in lexeme.data and 'Flags' in lexeme.data['Gram']:
            lexeme_dict['flags'] = lexeme.data['Gram']['Flags']
        # including flag inheritance from paradigms
        if lexeme.paradigm_data:
            for key in lexeme.paradigm_data.keys():
                if not lexeme.paradigm_data[key]:
                    lexeme_dict['flags'][key] = lexeme.paradigm_data[key]

        # Structural restrictions
        if lexeme.data and 'Gram' in lexeme.data and 'StructuralRestrictions' in lexeme.data['Gram']:
            lexeme_dict['struct_restr'] = lexeme.data['Gram']['StructuralRestrictions']

        # Inflection text
        if lexeme.data and 'Gram' in lexeme.data and 'Inflection' in lexeme.data['Gram']:
            lexeme_dict['infl_text'] = lexeme.data['Gram']['Inflection']

        # Free text
        if lexeme.data and 'Gram' in lexeme.data and 'FreeText' in lexeme.data['Gram']:
            lexeme_dict['free_text'] = lexeme.data['Gram']['FreeText']

        # Paradigms
        if lexeme.paradigm:
            lexeme_dict['paradigm'] = {'id': lexeme.paradigm}
            if lexeme.stem1:
                lexeme_dict['paradigm']['stem_inf'] = lexeme.stem1
            if lexeme.stem2:
                lexeme_dict['paradigm']['stem_pres'] = lexeme.stem2
            if lexeme.stem3:
                lexeme_dict['paradigm']['stem_past'] = lexeme.stem3

        result.append(lexeme_dict)
    return result


def fetch_main_lexeme(connection, lexeme_id, entry_human_key):
    if not lexeme_id:
        print(f'No primary lexeme id for entry {entry_human_key}!')
        return
    lex_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_primary_lex = f"""
SELECT l.id, lemma, paradigm_id, l.data, p.data as paradigm_data
FROM {db_connection_info['schema']}.lexemes l
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE l.id = {lexeme_id} and NOT l.hidden
"""
    lex_cursor.execute(sql_primary_lex)
    lexemes = lex_cursor.fetchall()
    if not lexemes or len(lexemes) < 1:
        print(f'No primary lexeme for entry {entry_human_key}!')
        return
    if len(lexemes) > 1:
        print(f'Too many primary lexemes for entry {entry_human_key}!')
    return lexemes[0]


def fetch_senses(connection, entry_id, parent_sense_id=None):
    if not entry_id:
        return
    sense_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    parent_sense_clause = 'is NULL'
    if parent_sense_id:
        parent_sense_clause = f"""= {parent_sense_id}"""
    sql_senses = f"""
SELECT id, gloss, order_no, parent_sense_id, synset_id
FROM {db_connection_info['schema']}.senses
WHERE entry_id = {entry_id} and parent_sense_id {parent_sense_clause} and NOT hidden
ORDER BY order_no
"""
    sense_cursor.execute(sql_senses)
    senses = sense_cursor.fetchall()
    if not senses:
        return
    result = []
    for sense in senses:
        # sense_data = json.loads(sense.data)
        subsenses = fetch_senses(connection, entry_id, sense.id)
        sense_dict = {'ord': sense.order_no, 'gloss': sense.gloss}
        if sense.synset_id:
            sense_dict['synset_id'] = sense.synset_id
            sense_dict['synset_senses'] = fetch_synset_info(connection, sense.synset_id)
            sense_dict['synset_rels'] = fetch_synset_relations(connection, sense.synset_id)
            sense_dict['gradset'] = fetch_gradset(connection, sense.synset_id)
        if subsenses:
            sense_dict['subsenses'] = subsenses
        result.append(sense_dict)
    return result


def fetch_synset_info(connection, synset_id):
    if not synset_id:
        return
    synset_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_senses = f"""
SELECT syn.id, s.id as sense_id, s.order_no as sense_no, e.human_key as entry_hk
FROM dict.synsets syn
RIGHT OUTER JOIN dict.senses s ON syn.id = s.synset_id
JOIN dict.entries e ON s.entry_id = e.id
WHERE syn.id = {synset_id} and NOT s.hidden
ORDER BY e.type_id, entry_hk
"""
    synset_cursor.execute(sql_synset_senses)
    synset_members = synset_cursor.fetchall()
    if not synset_members:
        return
    result = []
    for member in synset_members:
        result.append({'softid': f'{member.entry_hk}/{member.sense_no}', 'hardid': member.sense_id})
    return result


def fetch_synset_relations (connection, synset_id):
    if not synset_id:
        return
    result = []

    synset_rel_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_rels_1 = f"""
SELECT rel.id, rel.synset_1_id as other, tp.name_inverse as other_name, tp.relation_name as rel_name
FROM dict.synset_relations rel
JOIN dict.synset_rel_types tp ON rel.type_id = tp.id
WHERE rel.synset_2_id = {synset_id}
"""
    synset_rel_cursor.execute(sql_synset_rels_1)
    rel_members = synset_rel_cursor.fetchall()
    if rel_members:
        for member in rel_members:
            result.append({'other': member.other, 'other_name': member.other_name, 'relation': member.rel_name})

    sql_synset_rels_2 = f"""
SELECT rel.id, rel.synset_2_id as other, tp.name as other_name, tp.relation_name as rel_name
FROM dict.synset_relations rel
JOIN dict.synset_rel_types tp ON rel.type_id = tp.id
WHERE rel.synset_1_id = {synset_id}
"""

    synset_rel_cursor.execute(sql_synset_rels_2)
    rel_members = synset_rel_cursor.fetchall()
    if rel_members:
        for member in rel_members:
            result.append({'id': member.id, 'other': member.other, 'other_name': member.other_name,
                           'relation': member.rel_name})

    sorted_result = sorted(result, key=lambda item: (item['relation'], item['other_name'], item['other']))
    return sorted_result


def fetch_gradset (connection, member_synset_id):
    if not member_synset_id:
        return

    gradset_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_gradset = f"""
SELECT syn.id as synset_id, syn.gradset_id as gradset_id, grad.synset_id as gradset_cat
FROM  dict.synsets syn
JOIN dict.gradsets grad ON syn.gradset_id = grad.id
WHERE gradset_id = (
    SELECT gradset_id
    FROM dict.synsets
    WHERE ID = {member_synset_id}) AND gradset_id is not null
ORDER BY syn.id
"""
    gradset_cursor.execute(sql_gradset)
    gradet_members = gradset_cursor.fetchall()
    if not gradet_members:
        return

    result = {'gradset_id': gradet_members[0].gradset_id, 'gradset_cat': gradet_members[0].gradset_cat,
              'member_synsets': []}
    for member in gradet_members:
        result['member_synsets'].append(member.synset_id)
    return result

