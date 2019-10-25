#!/usr/bin/env python3
from db_config import db_connection_info

import psycopg2
from psycopg2.extras import NamedTupleCursor
from collections import Counter
import json

connection = None
attribute_stats = Counter()


def db_connect():
    global connection

    if db_connection_info is None or db_connection_info["host"] is None or len(db_connection_info["host"]) == 0:
        print("Postgres connection error: connection information must be supplied in db_config")
        raise Exception("Postgres connection error: connection information must be supplied in <conn_info>")

    print('Connecting to database %s' % (db_connection_info['dbname'],))
    schema = db_connection_info['schema'] or 'tezaurs'
    connection = psycopg2.connect(
            host=db_connection_info['host'],
            port=db_connection_info['port'],
            dbname=db_connection_info['dbname'],
            user=db_connection_info['user'],
            password=db_connection_info['password'],
            options=f'-c search_path={schema}',
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
    sql_entries = """
SELECT id, human_id, homonym_id, primary_lexeme_id, entry_type
FROM tezaurs.entries
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
                break
            result['lemma'] = lexeme.lemma
            senses = fetch_senses(row.id, row.human_id)
            if senses:
                result['senses'] = senses
            yield result
            counter = counter + 1
        print(f'{counter}\r')

def fetch_lexeme(lexeme_id, entry_human_id):
    if not lexeme_id:
        return
    lex_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_primary_lex = f'SELECT id, lemma FROM tezaurs.lexemes WHERE id = {lexeme_id}'
    lex_cursor.execute(sql_primary_lex)
    lexemes = lex_cursor.fetchall()
    if not lexemes:
        print(f'No primary lexeme for entry {entry_human_id}!\n')
        return
    if len(lexemes) > 1:
        print(f'Too many primary lexemes for entry {entry_human_id}!\n')
    return lexemes[0]

def fetch_senses(entry_id, entry_human_id):
    if not entry_id:
        return
    sense_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_senses = f'SELECT data, order_no, parent_sense_id FROM tezaurs.senses WHERE entry_id = {entry_id} and parent_sense_id is NULL ORDER BY order_no'
    sense_cursor.execute(sql_senses)
    senses = sense_cursor.fetchall()
    if not senses:
        return
    result = []
    for sense in senses:
        #sense_data = json.loads(sense.data)
        result.append({'id': sense.order_no, 'gloss': sense.data["Gloss"][0]["GlossText"]})
    return result

def dump_entries(filename):
    with open(filename, 'w', encoding='utf8') as f:
        f.write('<TEI>\n')
        f.write('\t<teiHeader>TODO</teiHeader>\n')
        f.write('\t<body>\n')
        for entry in fetch_entries():
            f.write(f'\t\t<entry id="{entry["id"]}">\n')
            f.write(f'\t\t\t<form type="lemma">{entry["lemma"]}</form>\n')
            if "senses" in entry:
                for sense in entry["senses"]:
                    f.write(f'\t\t\t\t<sense id="{sense["id"]}">\n')
                    f.write(f'\t\t\t\t\t<def>{sense["gloss"]}</def>\n')
                    f.write('\t\t\t\t</sense>\n')
            f.write('\t\t</entry>\n')
        f.write('\t</body>')
        f.write('</TEI>\n')

db_connect()

filename = 'tezaurs_tei.xml'
dump_entries(filename)
print(f'Done! Output written to {filename}')
