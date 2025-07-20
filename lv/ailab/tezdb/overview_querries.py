from lv.ailab.tezdb.db_config import db_connection_info
from lv.ailab.tezdb.query_uttils import extract_gram, extract_paradigm_stems
from lv.ailab.tezdb.single_entry_queries import fetch_lexemes, fetch_senses, fetch_examples, fetch_morpho_derivs
from lv.ailab.tezdb.subentry_queries import fetch_sources_by_esl_id

from psycopg2.extras import NamedTupleCursor


# TODO paprasīt P un sataisīt smukāk kveriju veidošanu.

# TODO
def get_dict_version(connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_dict_properties = f"""
    SELECT title, extract(YEAR from release_timestamp) as year, extract(MONTH from release_timestamp) as month,
        info->'dictionary' #>> '{{}}' as dictionary, info->'tag' #>> '{{}}' as tag,
        info->'counts'->'entries' #>> '{{}}' as entries,
        info->'counts'->'lexemes' #>> '{{}}' as lexemes,
        info->'counts'->'senses' #>> '{{}}' as senses,
        info->'title_short' #>> '{{}}' as title_short,
        info->'title_en' #>> '{{}}' as title_long,
        info->'release_name_en' #>> '{{}}' as release_name_en,
        info->'editors_en' #>> '{{}}' as editors_en,
        info->'copyright_en' #>> '{{}}' as copyright_en,
        info->'canonical_url' #>> '{{}}' as url
    FROM {db_connection_info['schema']}.metadata
"""
    cursor.execute(sql_dict_properties)
    row = cursor.fetchone()
    return {
        'dictionary': row.dictionary,
        'title_short': row.title_short, 'title_long': row.title_long,
        'tag': row.tag,
        'release_name_en': row.release_name_en, 'editors_en': row.editors_en, 'copyright_en': row.copyright_en,
        'entries': row.entries, 'lexemes': row.lexemes, 'senses': row.senses,
        'year': row.year, 'month': row.month,
        'url': row.url}


def fetch_all_sources(connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_dict_sources = f"""
        SELECT abbr, title, url
        FROM {db_connection_info['schema']}.sources
        ORDER BY abbr ASC
    """
    cursor.execute(sql_dict_sources)
    while True:
        rows = cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            yield {'abbr': row.abbr, 'title': row.title, 'url': row.url}


def fetch_all_entries(connection, omit_mwe=False, omit_wordparts=False, omit_pot_wordparts=False,
                      do_entrylevel_exmples=False):
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
ORDER BY type_id, heading, homonym_no
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
            gram_dict = extract_gram(row, None)
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
            if do_entrylevel_exmples:
                examples = fetch_examples(connection, row.id, True)
                if examples:
                    result['examples'] = examples
            sources = fetch_sources_by_esl_id(connection, row.id, None, None)
            if sources:
                result['sources'] = sources
            morpho_derivs = fetch_morpho_derivs(connection, row.id)
            if morpho_derivs:
                result['morpho_derivs'] = morpho_derivs
            yield result
        print(f'entries: {counter}\r')


def fetch_all_synseted_lexemes(connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_lexemes = f"""
SELECT l.id as id, l.entry_id as entry_id, l.lemma as lemma,
    l.data->'Gram'->'Flags'->>'Vārdšķira' as lex_pos,
    l.data->'Gram'->'Flags'->>'Saīsinājuma tips' as lex_abbr_type,
    p.data->>'Vārdšķira' as p_pos,
    p.data->>'Saīsinājuma tips' as p_abbr_type,
    p.human_key as paradigm, stem1, stem2, stem3, e.human_key as entry_hk
FROM {db_connection_info['schema']}.lexemes as l
JOIN {db_connection_info['schema']}.lexeme_types lt on l.type_id = lt.id
LEFT JOIN {db_connection_info['schema']}.paradigms p on l.paradigm_id = p.id
JOIN {db_connection_info['schema']}.entries e on l.entry_id = e.id
JOIN {db_connection_info['schema']}.senses s on l.entry_id = s.entry_id
WHERE s.synset_id <> 0 and NOT l.hidden and NOT s.hidden and NOT e.hidden and
    (lt.name = 'default' or lt.name = 'alternativeSpelling' or lt.name = 'abbreviation')
GROUP BY l.id, paradigm, p_pos, p_abbr_type, entry_hk
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
            result = {'id': row.id, 'entry': row.entry_hk, 'lemma': row.lemma, 'pos': row.p_pos,
                      'abbr_type': row.p_abbr_type}
            if hasattr(row, 'paradigm') and row.paradigm:
                result['paradigm'] = extract_paradigm_stems(row)

            if row.lex_pos:
                result['pos'] = row.lex_pos
            if row.lex_abbr_type:
                result['abbr_type'] = row.lex_abbr_type
            yield result
        print(f'lexemes: {counter}\r')


def fetch_all_synsets(connection):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset = f"""
SELECT syn.id
FROM {db_connection_info['schema']}.synsets as syn
JOIN {db_connection_info['schema']}.senses as s ON syn.id = s.synset_id
GROUP BY syn.id
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

def fetch_all_paradigms(connection):
    result = {}
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_paradigms = f"""
SELECT id, data as flags, human_key as paradigm
FROM {db_connection_info['schema']}.paradigms
ORDER BY human_key ASC
"""
    cursor.execute(sql_paradigms)
    paradigm_data = cursor.fetchall()
    for p in paradigm_data:
        result[p.paradigm] = p.flags

    return result
