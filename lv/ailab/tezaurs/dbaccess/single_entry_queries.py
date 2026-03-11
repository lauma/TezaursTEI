from psycopg2.extras import NamedTupleCursor

from lv.ailab.tezaurs.dbaccess.db_config import db_connection_info
from lv.ailab.tezaurs.dbaccess.query_uttils import extract_gram
from lv.ailab.tezaurs.dbobjects.sources import DictSource


def fetch_lexemes(connection, entry_id, main_lex_id):
    if not entry_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_senses = f"""
SELECT l.id, lemma, lt.name as lexeme_type, p.human_key as paradigm, stem1, stem2, stem3,
    l.data, p.data as paradigm_data, hidden
FROM {db_connection_info['schema']}.lexemes l
JOIN {db_connection_info['schema']}.lexeme_types lt ON l.type_id = lt.id
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE entry_id = {entry_id} and (NOT hidden or reason_for_hiding='not-public')
ORDER BY (l.id!={main_lex_id}), order_no
"""
    cursor.execute(sql_senses)
    lexemes = cursor.fetchall()
    if not lexemes:
        return
    result = []
    for lexeme in lexemes:
        lexeme_dict = {'lemma': lexeme.lemma, 'type': lexeme.lexeme_type, 'id': lexeme.id, 'hidden': lexeme.hidden}

        if lexeme.data and 'Pronunciations' in lexeme.data:
            lexeme_dict['pronun'] = lexeme.data['Pronunciations']

        gram_dict = extract_gram(lexeme, {'Stems', 'Morfotabulas tips', 'Paradigmas īpatnības'})
        lexeme_dict.update(gram_dict)
        lexeme_dict['sources'] = DictSource.fetch_sources_by_esl_id(connection, None, lexeme.id, None)
        result.append(lexeme_dict)
    return result


def fetch_main_lexeme(connection, lexeme_id, entry_human_key):
    if not lexeme_id:
        print(f'No primary lexeme id for entry {entry_human_key}!')
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_primary_lex = f"""
SELECT l.id, lemma, hidden, paradigm_id, l.data, p.data as paradigm_data
FROM {db_connection_info['schema']}.lexemes l
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE l.id = {lexeme_id} and (NOT hidden or reason_for_hiding='not-public')
"""
    cursor.execute(sql_primary_lex)
    lexemes = cursor.fetchall()
    if not lexemes or len(lexemes) < 1:
        print(f'No primary lexeme for entry {entry_human_key}!')
        return
    if len(lexemes) > 1:
        print(f'Too many primary lexemes for entry {entry_human_key}!')
    return lexemes[0]


def fetch_morpho_derivs(connection, entry_id):
    if not entry_id:
        return
    result = []
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_derivs_from = f"""
SELECT er.id, ert.name, ert.name_inverse, e2.human_key, er.data as data, er.hidden
FROM dict.entry_relations er
JOIN dict.entry_rel_types ert on type_id = ert.id
JOIN dict.entries e2 on entry_2_id = e2.id
WHERE entry_1_id = {entry_id} and ert.name = 'derivativeOf'
      and (NOT er.hidden or er.reason_for_hiding='not-public')
      and (NOT e2.hidden or e2.reason_for_hiding='not-public')
"""
    cursor.execute(sql_derivs_from)
    derivs_from = cursor.fetchall()
    for deriv in derivs_from:
        deriv_dict = {'my_role': deriv.name, 'target_role': deriv.name_inverse,
                      'target_softid': deriv.human_key, 'hidden': deriv.hidden}
        gram_dict = extract_gram(deriv)
        deriv_dict.update(gram_dict)
        result.append(deriv_dict)

    sql_derivs_to = f"""
SELECT er.id, ert.name, ert.name_inverse, e1.human_key, er.data as data, er.hidden
FROM dict.entry_relations er
JOIN dict.entry_rel_types ert on type_id = ert.id
JOIN dict.entries e1 on entry_1_id = e1.id
WHERE entry_2_id = {entry_id} and ert.name = 'derivativeOf'
      and (NOT er.hidden or er.reason_for_hiding='not-public')
      and (NOT e1.hidden or e1.reason_for_hiding='not-public')
"""
    cursor.execute(sql_derivs_to)
    derivs_to = cursor.fetchall()
    for deriv in derivs_to:
        deriv_dict = {'my_role': deriv.name_inverse, 'target_role': deriv.name,
                      'target_softid': deriv.human_key, 'hidden': deriv.hidden}
        # 2024-09-19 ar valodniekiem WN seminārā tiek runāts, ka loģiskāk ir formantu un celma informāciju redzēt pie
        # atvasinājuma, nevis atvasināmā.
        #gram_dict = extract_gram(deriv)
        #deriv_dict.update(gram_dict)
        result.append(deriv_dict)

    sorted_result = sorted(result, key=lambda item: (not item['hidden'], item['my_role'], item['target_role'], item['target_softid']))
    return sorted_result
