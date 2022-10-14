from psycopg2.extras import NamedTupleCursor

from lv.ailab.tezdb.db_config import db_connection_info


def fetch_synset_senses(connection, synset_id):
    if not synset_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_senses = f"""
SELECT syn.id, s.id as sense_id, s.order_no as sense_no, s.gloss as gloss, e.human_key as entry_hk
FROM {db_connection_info['schema']}.synsets syn
RIGHT OUTER JOIN dict.senses s ON syn.id = s.synset_id
JOIN {db_connection_info['schema']}.entries e ON s.entry_id = e.id
WHERE syn.id = {synset_id} and NOT s.hidden
ORDER BY e.type_id, entry_hk
"""
    cursor.execute(sql_synset_senses)
    synset_members = cursor.fetchall()
    if not synset_members:
        return
    result = []
    for member in synset_members:
        result.append({'softid': f'{member.entry_hk}/{member.sense_no}',
                       'hardid': member.sense_id, 'gloss': member.gloss})
    return result


def fetch_synset_relations(connection, synset_id):
    if not synset_id:
        return
    result = []

    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_rels_1 = f"""
SELECT rel.id, rel.synset_1_id as other, tp.name_inverse as other_name, tp.relation_name as rel_name
FROM {db_connection_info['schema']}.synset_relations rel
JOIN {db_connection_info['schema']}.synset_rel_types tp ON rel.type_id = tp.id
WHERE rel.synset_2_id = {synset_id}
"""
    cursor.execute(sql_synset_rels_1)
    rel_members = cursor.fetchall()
    if rel_members:
        for member in rel_members:
            result.append({'id': member.id, 'other': member.other, 'other_name': member.other_name,
                           'relation': member.rel_name})

    sql_synset_rels_2 = f"""
SELECT rel.id, rel.synset_2_id as other, tp.name as other_name, tp.relation_name as rel_name
FROM {db_connection_info['schema']}.synset_relations rel
JOIN {db_connection_info['schema']}.synset_rel_types tp ON rel.type_id = tp.id
WHERE rel.synset_1_id = {synset_id}
"""

    cursor.execute(sql_synset_rels_2)
    rel_members = cursor.fetchall()
    if rel_members:
        for member in rel_members:
            result.append({'id': member.id, 'other': member.other, 'other_name': member.other_name,
                           'relation': member.rel_name})

    sorted_result = sorted(result, key=lambda item: (item['relation'], item['other_name'], item['other']))
    return sorted_result


def fetch_gradset(connection, member_synset_id):
    if not member_synset_id:
        return

    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_gradset = f"""
SELECT syn.id as synset_id, syn.gradset_id as gradset_id, grad.synset_id as gradset_cat
FROM  {db_connection_info['schema']}.synsets syn
JOIN {db_connection_info['schema']}.gradsets grad ON syn.gradset_id = grad.id
WHERE gradset_id = (
    SELECT gradset_id
    FROM {db_connection_info['schema']}.synsets
    WHERE ID = {member_synset_id}) AND gradset_id is not null
ORDER BY syn.id
"""
    cursor.execute(sql_gradset)
    gradet_members = cursor.fetchall()
    if not gradet_members:
        return

    result = {'gradset_id': gradet_members[0].gradset_id, 'gradset_cat': gradet_members[0].gradset_cat,
              'member_synsets': []}
    for member in gradet_members:
        result['member_synsets'].append(member.synset_id)
    return result


def fetch_synset_lexemes(connection, synset_id):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_lexemes = f"""
SELECT syn.id,
    l.id as lexeme_id, l.lemma as lemma, e.human_key as entry_hk
FROM {db_connection_info['schema']}.synsets syn
RIGHT OUTER JOIN {db_connection_info['schema']}.senses s ON syn.id = s.synset_id
RIGHT OUTER JOIN {db_connection_info['schema']}.lexemes l ON s.entry_id = l.entry_id
JOIN {db_connection_info['schema']}.lexeme_types lt on l.type_id = lt.id
JOIN {db_connection_info['schema']}.entries e ON s.entry_id = e.id
WHERE syn.id = {synset_id} and NOT s.hidden and NOT l.hidden and NOT e.hidden and
    (lt.name = 'default' or lt.name = 'alternativeSpelling' or lt.name = 'abbreviation')
ORDER BY e.type_id, entry_hk
"""
    cursor.execute(sql_synset_lexemes)
    lexemes = cursor.fetchall()
    result = []
    for lexeme in lexemes:
        result.append({'lexeme_id': lexeme.lexeme_id, 'lemma': lexeme.lemma, 'entry': lexeme.entry_hk})
    return result


def fetch_omw_eq_relations(connection, synset_id):
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_lexemes = f"""
SELECT syn.id as synset_id, el.url as url, el.remote_id as remote_id
FROM {db_connection_info['schema']}.synsets syn
JOIN {db_connection_info['schema']}.synset_external_links el ON syn.id = el.synset_id
JOIN {db_connection_info['schema']}.external_link_types lt ON el.link_type_id = lt.id
WHERE syn.id = {synset_id} and lt.name = 'omw' and el.data is null
ORDER BY el.remote_id
"""
    cursor.execute(sql_synset_lexemes)
    rels = cursor.fetchall()
    result = []
    for rel in rels:
        result.append(rel.remote_id)
    return result
