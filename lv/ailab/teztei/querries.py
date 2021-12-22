from psycopg2.extras import NamedTupleCursor

from lv.ailab.teztei.db_config import db_connection_info

# TODO paprasīt P un sataisīt smukāk kveriju veidošanu.

def query(sql, parameters, connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    cursor.execute(sql, parameters)
    r = cursor.fetchall()
    cursor.close()
    return r


def fetch_entries(connection, omit_pot_wordparts):
    entry_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    where_clause = """et.name = 'word'"""
    if not omit_pot_wordparts:
        where_clause = where_clause + """ or et.name = 'wordPart'"""
    sql_entries = f"""
SELECT e.id, type_id, name as type_name, human_key, homonym_no, primary_lexeme_id, e.data->>'Etymology' as etym
FROM {db_connection_info['schema']}.entries e
JOIN {db_connection_info['schema']}.entry_types et ON e.type_id = et.id
WHERE ({where_clause}) and NOT e.hidden
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
            result = {'id': row.human_key, 'hom_id': row.homonym_no, 'type': row.type_name}
            if row.etym:
                result['etym'] = row.etym
            lexeme = fetch_lexeme(connection, row.primary_lexeme_id, row.human_key)
            if not lexeme:
                continue
            if omit_pot_wordparts and (row.type_name == 'wordPart' or lexeme.lemma.startswith('-') or lexeme.lemma.endswith('-')):
                continue
            result['lemma'] = lexeme.lemma
            if lexeme.paradigm_data and 'Vārdšķira' in lexeme.paradigm_data:
                result['pos'] = [lexeme.paradigm_data['Vārdšķira']]
                if 'Reziduāļa tips' in lexeme.paradigm_data:
                    #result['pos'] = result['pos'] + lexeme.paradigm_data['Reziduāļa tips']
                    result['pos'].append(lexeme.paradigm_data['Reziduāļa tips'])
                # FIXME izņemt pēc DB update
                if 'Darbības vārda tips' in lexeme.paradigm_data:
                    result['pos'].append('Darbības vārds')
            if lexeme.data and 'Gram' in lexeme.data:
                gram = lexeme.data['Gram']
                if 'Flags' in gram and 'Kategorija' in gram['Flags'] and gram['Flags']['Kategorija']:
                    result['pos'] = gram['Flags']['Kategorija']
                if 'Flags' in gram and 'Citi' in gram['Flags'] and 'Neviennozīmīga vārdšķira vai kategorija' in gram['Flags']['Citi']:
                    result['pos'] = []
                if 'FlagText' in gram and db_connection_info['schema'] != 'tezaurs':
                    result['pos_text'] = gram['FlagText']
                if 'FreeText' in gram and db_connection_info['schema'] != 'tezaurs':
                    result['pos_text'] = gram['FreeText']
            if lexeme.data and 'Pronunciations' in lexeme.data:
                result['pronun'] = lexeme.data['Pronunciations']
            senses = fetch_senses(connection, row.id)
            if senses:
                result['senses'] = senses
            yield result
        print(f'{counter}\r')


def fetch_lexeme(connection, lexeme_id, entry_human_key):
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
        if subsenses:
            sense_dict['subsenses'] = subsenses
        result.append(sense_dict)
    return result


def fetch_synset_info (connection, synset_id):
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