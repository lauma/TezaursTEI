from psycopg2.extras import NamedTupleCursor
from lv.ailab.tezdb.db_config import db_connection_info


def fetch_examples(connection, parent_id, entry_level_samples=False):
    if not parent_id:
        return
    where_clause = "sense_id"
    if entry_level_samples:
        where_clause = 'entry_id'
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_samples = f"""
SELECT id, content, data->>'CitedSource' as source, (data->>'TokenLocation')::int as location, hidden
FROM {db_connection_info['schema']}.examples
WHERE {where_clause} = {parent_id}
ORDER BY hidden DESC, order_no
"""
    cursor.execute(sql_samples)
    samples = cursor.fetchall()
    if not samples:
        return
    result = []
    for sample in samples:
        sample_dict = {'text': sample.content, 'hidden': sample.hidden}
        if sample.source:
            sample_dict['source'] = sample.source
        if sample.location and sample.location is not None:
            sample_dict['location'] = sample.location
        result.append(sample_dict)
    return result


def fetch_gloss_entry_links(connection, sense_id):
    if not sense_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_links = f"""
SELECT r.id, e.human_key
FROM {db_connection_info['schema']}.sense_entry_relations r
JOIN {db_connection_info['schema']}.sense_entry_rel_types rt on r.type_id = rt.id
JOIN {db_connection_info['schema']}.entries e on r.entry_id = e.id
WHERE rt.name = 'hasGlossLink' and NOT e.hidden and r.sense_id={sense_id}
"""
    cursor.execute(sql_links)
    gloss_links = cursor.fetchall()
    if not gloss_links:
        return
    result = {}
    for gloss_link in gloss_links:
        result[gloss_link.id] = gloss_link.human_key
    return result


def fetch_gloss_sense_links(connection, sense_id):
    if not sense_id:
        return
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_links = f"""
SELECT r.id, s.order_no as sense_order, ps.order_no as parent_order, e.human_key
FROM {db_connection_info['schema']}.sense_relations r
JOIN {db_connection_info['schema']}.sense_rel_types rt on r.type_id = rt.id
JOIN {db_connection_info['schema']}.senses s on r.sense_2_id = s.id
LEFT JOIN {db_connection_info['schema']}.senses ps on s.parent_sense_id = ps.id
JOIN {db_connection_info['schema']}.entries e on s.entry_id = e.id
WHERE rt.name = 'hasGlossLink' and NOT e.hidden and NOT s.hidden and (ps.hidden is NULL or NOT ps.hidden)
      and r.sense_1_id={sense_id}
"""
    cursor.execute(sql_links)
    gloss_links = cursor.fetchall()
    if not gloss_links:
        return
    result = {}
    for gloss_link in gloss_links:
        endpoint = gloss_link.human_key
        if gloss_link.parent_order and gloss_link.parent_order is not None:
            endpoint = endpoint + '/' + str(gloss_link.parent_order)
        endpoint = endpoint + '/' + str(gloss_link.sense_order)
        result[gloss_link.id] = endpoint
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
