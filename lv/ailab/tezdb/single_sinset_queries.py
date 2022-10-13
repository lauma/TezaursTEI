from psycopg2.extras import NamedTupleCursor


def fetch_synset_info(connection, synset_id):
    if not synset_id:
        return
    synset_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_synset_senses = f"""
SELECT syn.id, s.id as sense_id, s.order_no as sense_no, s.gloss as gloss, e.human_key as entry_hk
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


def fetch_synset_relations(connection, synset_id):
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


def fetch_gradset(connection, member_synset_id):
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
