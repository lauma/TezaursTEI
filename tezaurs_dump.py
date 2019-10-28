#!/usr/bin/env python3
from db_config import db_connection_info

import psycopg2
from psycopg2.extras import NamedTupleCursor
import sys

connection = None
schema = None


def db_connect():
    global connection
    global schema

    if db_connection_info is None or db_connection_info["host"] is None or len(db_connection_info["host"]) == 0:
        print("Postgres connection error: connection information must be supplied in db_config")
        raise Exception("Postgres connection error: connection information must be supplied in <conn_info>")

    if schema:
        db_connection_info['schema'] = schema
    else:
        schema = db_connection_info['schema']
    print(f'Connecting to database {db_connection_info["dbname"]}, schema {db_connection_info["schema"]}')
    connection = psycopg2.connect(
            host=db_connection_info['host'],
            port=db_connection_info['port'],
            dbname=db_connection_info['dbname'],
            user=db_connection_info['user'],
            password=db_connection_info['password'],
            options=f'-c search_path={db_connection_info["schema"]}',
        )


def query(sql, parameters):
    global connection
    cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    cursor.execute(sql, parameters)
    r = cursor.fetchall()
    cursor.close()
    return r


def fetch_entries():
    global connection
    entry_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_entries = f"""
SELECT e.id, type_id, name as type_name, human_id, homonym_id, primary_lexeme_id
FROM {db_connection_info['schema']}.entries e
JOIN {db_connection_info['schema']}.entry_types et ON e.type_id = et.id
WHERE et.name = 'word'
ORDER BY human_id
"""
    # TODO - filtrs uz e.release_id lai ņemtu svaigāko relīzi nevis visas

    entry_cursor.execute(sql_entries)
    counter = 0
    while True:
        rows = entry_cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            result = {'id': row.human_id}
            lexeme = fetch_lexeme(row.primary_lexeme_id, row.human_id)
            if not lexeme:
                continue
            result['lemma'] = lexeme.lemma
            if lexeme.data and 'Gram' in lexeme.data:
                gram = lexeme.data['Gram']
                if 'Flags' in gram and 'Kategorija' in gram['Flags'] and not(
                        'Citi' in gram['Flags'] and
                        'Neviennozīmīga vārdšķira vai kategorija' in gram['Flags']['Citi']):
                    result['pos'] = gram['Flags']['Kategorija']
                elif 'FlagText' in gram:
                    result['pos_text'] = gram['FlagText']
                elif 'FreeText' in gram and db_connection_info['schema'] != 'tezaurs':
                    result['pos_text'] = gram['FreeText']
            senses = fetch_senses(row.id, row.human_id)
            if senses:
                result['senses'] = senses
            yield result
            counter = counter + 1
        print(f'{counter}\r')


def fetch_lexeme(lexeme_id, entry_human_id):
    if not lexeme_id:
        print(f'No primary lexeme id for entry {entry_human_id}!')
        return
    lex_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_primary_lex = f"""
SELECT id, lemma, data
FROM {db_connection_info['schema']}.lexemes
WHERE id = {lexeme_id}
"""
    lex_cursor.execute(sql_primary_lex)
    lexemes = lex_cursor.fetchall()
    if not lexemes or len(lexemes) < 1:
        print(f'No primary lexeme for entry {entry_human_id}!')
        return
    if len(lexemes) > 1:
        print(f'Too many primary lexemes for entry {entry_human_id}!')
    return lexemes[0]


def fetch_senses(entry_id, entry_human_id):
    if not entry_id:
        return
    sense_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_senses = f"""
SELECT gloss, order_no, parent_sense_id FROM {db_connection_info['schema']}.senses
WHERE entry_id = {entry_id} and parent_sense_id is NULL
ORDER BY order_no
"""
    sense_cursor.execute(sql_senses)
    senses = sense_cursor.fetchall()
    if not senses:
        return
    result = []
    for sense in senses:
        #sense_data = json.loads(sense.data)
        result.append({'id': sense.order_no, 'gloss': sense.gloss})
    return result


def dump_entries(filename):
    global schema
    with open(filename, 'w', encoding='utf8') as f:
        f.write('<TEI>\n')
        f.write('\t<teiHeader>TODO</teiHeader>\n')
        f.write('\t<body>\n')
        for entry in fetch_entries():
            f.write(f'\t\t<entry id="{schema}/{entry["id"]}">\n')
            f.write(f'\t\t\t<form type="lemma">{entry["lemma"]}</form>\n')
            if 'pos' in entry or 'pos_text' in entry:
                f.write('\t\t\t\t<gramGrp>\n')
                if 'pos' in entry:
                    for g in entry['pos']:
                        f.write(f'\t\t\t\t\t<gram>{g}</gram>\n')
                    #f.write(f'\t\t\t\t\t<gram>{"; ".join(entry["pos"])}</gram>\n')
                elif 'pos_text' in entry:
                    f.write(f'\t\t\t\t\t<gram>{entry["pos_text"]}</gram>\n')
                f.write('\t\t\t\t</gramGrp>\n')
            if 'senses' in entry:
                for sense in entry["senses"]:
                    f.write(f'\t\t\t\t<sense id="{schema}/{entry["id"]}/{sense["id"]}">\n')
                    f.write(f'\t\t\t\t\t<def>{sense["gloss"]}</def>\n')
                    f.write('\t\t\t\t</sense>\n')
            f.write('\t\t</entry>\n')
        f.write('\t</body>')
        f.write('</TEI>\n')


if len(sys.argv) > 1:
    schema = sys.argv[1]
db_connect()
filename = f'{db_connection_info["schema"]}_tei.xml'
dump_entries(filename)
print(f'Done! Output written to {filename}')
