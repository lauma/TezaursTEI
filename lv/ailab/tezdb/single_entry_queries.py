import regex
from psycopg2.extras import NamedTupleCursor

from lv.ailab.tezdb.db_config import db_connection_info
from lv.ailab.tezdb.query_uttils import extract_gram
from lv.ailab.tezdb.single_sinset_queries import fetch_synset_senses, fetch_synset_relations, fetch_gradset
from lv.ailab.tezdb.subentry_queries import fetch_examples, fetch_gloss_entry_links, fetch_gloss_sense_links, \
    fetch_sources_by_esl_id, fetch_semantic_derivs_by_sense


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
        sources = fetch_sources_by_esl_id(connection, None, lexeme.id, None)
        if sources:
            lexeme_dict['sources'] = sources
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
        examples = fetch_examples(connection, sense.id)
        if examples:
            sense_dict['examples'] = examples
        sem_derivs = fetch_semantic_derivs_by_sense(connection, sense.id)
        if (sem_derivs):
            sense_dict['sem_derivs'] = sem_derivs
        sources = fetch_sources_by_esl_id(connection, None, None, sense.id)
        if sources:
            sense_dict['sources'] = sources

        if regex.search(r'\[((?:\p{L}\p{M}*)+)\]\{e:\d+\}', sense.gloss):
            gloss_entry_links = fetch_gloss_entry_links(connection, sense.id)
            if gloss_entry_links:
                sense_dict['ge_links'] = gloss_entry_links
        if regex.search(r'\[((?:\p{L}\p{M}*)+)\]\{s:\d+\}', sense.gloss):
            gloss_sense_links = fetch_gloss_sense_links(connection, sense.id)
            if gloss_sense_links:
                sense_dict['gs_links'] = gloss_sense_links

        result.append(sense_dict)
    return result

