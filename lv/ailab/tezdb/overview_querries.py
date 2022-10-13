from lv.ailab.tezdb.db_config import db_connection_info
from lv.ailab.tezdb.query_uttils import extract_gram
from lv.ailab.tezdb.single_entry_queries import fetch_lexemes, fetch_senses

from psycopg2.extras import NamedTupleCursor


# TODO paprasīt P un sataisīt smukāk kveriju veidošanu.
def fetch_entries(connection, omit_mwe=False, omit_wordparts=False, omit_pot_wordparts=False):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    where_clause = ""
    if omit_mwe or omit_wordparts:
        where_clause = """et.name = 'word'"""
        if not omit_wordparts:
            where_clause = where_clause + """ or et.name = 'wordPart'"""
        if not omit_mwe:
            where_clause = where_clause + """ or et.name = 'mwe'"""
        where_clause = '(' + where_clause + ')' + " and"
    sql_entries = f"""
SELECT e.id, type_id, name as type_name, heading, human_key, homonym_no,
    primary_lexeme_id, e.data->>'Etymology' as etym, e.data as data
FROM {db_connection_info['schema']}.entries e
JOIN {db_connection_info['schema']}.entry_types et ON e.type_id = et.id
WHERE {where_clause} NOT e.hidden
ORDER BY type_id, heading
"""
    cursor.execute(sql_entries)
    counter = 0
    while True:
        rows = cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            counter = counter + 1
            result = {'id': row.human_key, 'hom_id': row.homonym_no, 'type': row.type_name, 'headword': row.heading}
            if row.etym:
                result['etym'] = row.etym
            gram_dict = extract_gram(row)
            result.update(gram_dict)

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
            # prim_lex = {'lemma': primary_lexeme.lemma}
            # result['mainLexeme'] = prim_lex
            senses = fetch_senses(connection, row.id)
            if senses:
                result['senses'] = senses
            yield result
        print(f'entries: {counter}\r')


def fetch_synseted_lexemes(connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_lexemes = f"""
SELECT l.id as id, l.entry_id as entry_id, l.lemma as lemma,
    p.human_key as paradigm, e.human_key as entry_human_key
FROM {db_connection_info['schema']}.lexemes as l
JOIN {db_connection_info['schema']}.lexeme_types lt on l.type_id = lt.id
JOIN {db_connection_info['schema']}.paradigms p on l.paradigm_id = p.id
JOIN {db_connection_info['schema']}.entries e on l.entry_id = e.id
JOIN {db_connection_info['schema']}.senses s ON l.entry_id = s.entry_id
WHERE s.synset_id <> 0 AND NOT l.hidden AND NOT s.hidden AND 
    (lt.name = 'default' OR lt.name = 'alternativeSpelling' OR lt.name = 'abbreviation')
GROUP BY l.id, p.human_key, e.human_key
ORDER BY l.lemma ASC
"""
    cursor.execute(sql_synset_lexemes)
    counter = 0
    while True:
        rows = cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            counter = counter + 1
            result = {'id': row.id, 'entry': row.entry_human_key, 'lemma': row.lemma, 'paradigm': row.paradigm}
            yield result
        print(f'lexemes: {counter}\r')


def fetch_synsets(connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset = f"""
SELECT id
FROM {db_connection_info['schema']}.synsets
ORDER BY id ASC 
"""
    cursor.execute(sql_synset)
    counter = 0
    while True:
        rows = cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            counter = counter + 1
            yield row.id
        print(f'synsets: {counter}\r')
