from psycopg2.extras import NamedTupleCursor

from lv.ailab.tezdb.db_config import db_connection_info
from lv.ailab.tezdb.query_uttils import extract_gram
from lv.ailab.tezdb.single_sinset_queries import fetch_synset_senses, fetch_synset_relations, fetch_gradset


def fetch_lexemes(connection, entry_id, main_lex_id):
    if not entry_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_senses = f"""
SELECT l.id, lemma, lt.name as lexeme_type, p.human_key as paradigm, stem1, stem2, stem3,
    l.data, p.data as paradigm_data 
FROM {db_connection_info['schema']}.lexemes l
JOIN {db_connection_info['schema']}.lexeme_types lt ON l.type_id = lt.id
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE entry_id = {entry_id} and NOT hidden
ORDER BY (l.id!={main_lex_id}), order_no
"""
    cursor.execute(sql_senses)
    lexemes = cursor.fetchall()
    if not lexemes:
        return
    result = []
    for lexeme in lexemes:
        lexeme_dict = {'lemma': lexeme.lemma, 'type': lexeme.lexeme_type}

        if lexeme.data and 'Pronunciations' in lexeme.data:
            lexeme_dict['pronun'] = lexeme.data['Pronunciations']

        gram_dict = extract_gram(lexeme, {'Stems'})
        lexeme_dict.update(gram_dict)
        result.append(lexeme_dict)
    return result


def fetch_main_lexeme(connection, lexeme_id, entry_human_key):
    if not lexeme_id:
        print(f'No primary lexeme id for entry {entry_human_key}!')
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_primary_lex = f"""
SELECT l.id, lemma, paradigm_id, l.data, p.data as paradigm_data
FROM {db_connection_info['schema']}.lexemes l
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE l.id = {lexeme_id} and NOT l.hidden
"""
    cursor.execute(sql_primary_lex)
    lexemes = cursor.fetchall()
    if not lexemes or len(lexemes) < 1:
        print(f'No primary lexeme for entry {entry_human_key}!')
        return
    if len(lexemes) > 1:
        print(f'Too many primary lexemes for entry {entry_human_key}!')
    return lexemes[0]


def fetch_senses(connection, entry_id, parent_sense_id=None):
    if not entry_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    parent_sense_clause = 'is NULL'
    if parent_sense_id:
        parent_sense_clause = f"""= {parent_sense_id}"""
    sql_senses = f"""
SELECT id, gloss, order_no, parent_sense_id, synset_id, data
FROM {db_connection_info['schema']}.senses
WHERE entry_id = {entry_id} and parent_sense_id {parent_sense_clause} and NOT hidden
ORDER BY order_no
"""
    cursor.execute(sql_senses)
    senses = cursor.fetchall()
    if not senses:
        return
    result = []
    for sense in senses:
        # sense_data = json.loads(sense.data)
        subsenses = fetch_senses(connection, entry_id, sense.id)
        sense_dict = {'ord': sense.order_no, 'gloss': sense.gloss}
        gram_dict = extract_gram(sense, None)
        sense_dict.update(gram_dict)
        if sense.synset_id:
            sense_dict['synset_id'] = sense.synset_id
            sense_dict['synset_senses'] = fetch_synset_senses(connection, sense.synset_id)
            sense_dict['synset_rels'] = fetch_synset_relations(connection, sense.synset_id)
            sense_dict['gradset'] = fetch_gradset(connection, sense.synset_id)
        if subsenses:
            sense_dict['subsenses'] = subsenses
        result.append(sense_dict)
    return result


def fetch_entry_sources(connection, entry_id):
    if not entry_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_sources = f"""
    SELECT abbr, data->'sourceDetails' as details
    FROM {db_connection_info['schema']}.source_links scl
    JOIN {db_connection_info['schema']}.sources sc ON scl.source_id = sc.id
    WHERE entry_id = {entry_id}
    ORDER BY order_no
    """
    cursor.execute(sql_sources)
    sources = cursor.fetchall()
    if not sources:
        return
    result = []
    for source in sources:
        source_dict = {'abbr': source.abbr, 'details': source.details}
        result.append(source_dict)
    return result


def fetch_synseted_senses_by_lexeme(connection, lexeme_id):
    if not lexeme_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_senses = f"""
SELECT s.id as sense_id, s.synset_id
FROM {db_connection_info['schema']}.senses s
JOIN {db_connection_info['schema']}.lexemes l on s.entry_id = l.entry_id
WHERE l.id = {lexeme_id} AND s.synset_id<>0 AND NOT s.hidden
"""
    cursor.execute(sql_senses)
    senses = cursor.fetchall()
    if not senses:
        return
    result = []
    for s in senses:
        result.append({'sense_id': s.sense_id, 'synset_id': s.synset_id})
    return result
