#!/usr/bin/env python3
from lv.ailab.teztei.whitelist import EntryWhitelist
from lv.ailab.teztei.db_config import db_connection_info

import psycopg2
from psycopg2.extras import NamedTupleCursor
import sys
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

connection = None
dbname = None
whitelist = None

omit_pot_wordparts = False

def db_connect():
    global connection
    global dbname

    if db_connection_info is None or db_connection_info["host"] is None or len(db_connection_info["host"]) == 0:
        print("Postgres connection error: connection information must be supplied in db_config")
        raise Exception("Postgres connection error: connection information must be supplied in <conn_info>")

    if dbname:
        db_connection_info['dbname'] = dbname
    else:
        dbname = db_connection_info['dbname']
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
    where_clause = """et.name = 'word'"""
    if not omit_pot_wordparts:
        where_clause = where_clause + """ or et.name = 'wordPart'"""
    sql_entries = f"""
SELECT e.id, type_id, name as type_name, human_key, homonym_no, primary_lexeme_id, e.data->>'Etymology' as etym
FROM {db_connection_info['schema']}.entries e
JOIN {db_connection_info['schema']}.entry_types et ON e.type_id = et.id
WHERE {where_clause}
ORDER BY human_key
"""
    # TODO - filtrs uz e.release_id lai ņemtu svaigāko relīzi nevis visas

    entry_cursor.execute(sql_entries)
    counter = 0
    while True:
        rows = entry_cursor.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            counter = counter + 1
            result = {'id': row.human_key, 'hom_id': row.homonym_no, 'type': row.type_name}
            if row.etym:
                result['etym'] = row.etym
            lexeme = fetch_lexeme(row.primary_lexeme_id, row.human_key)
            if not lexeme:
                continue
            if omit_pot_wordparts and (row.type_name == 'wordPart' or lexeme.lemma.startswith('-') or lexeme.lemma.endswith('-')):
                continue
            result['lemma'] = lexeme.lemma
            if lexeme.paradigm_data and 'Vārdšķira' in lexeme.paradigm_data:
                result['pos'] = [lexeme.paradigm_data['Vārdšķira']]
                if 'Reziduāļa tips' in lexeme.paradigm_data:
                    #result['pos'] = result['pos'] + lexeme.paradigm_data['Reziduāļa tips']
                    result['pos'].append(lexeme.paradigm_data['Reziduāļa tips'])
                # FIXME izņemt pēc DB update
                if 'Darbības vārda tips' in lexeme.paradigm_data:
                    result['pos'].append('Darbības vārds')
            if lexeme.data and 'Gram' in lexeme.data:
                gram = lexeme.data['Gram']
                if 'Flags' in gram and 'Kategorija' in gram['Flags'] and gram['Flags']['Kategorija']:
                    result['pos'] = gram['Flags']['Kategorija']
                if 'Flags' in gram and 'Citi' in gram['Flags'] and 'Neviennozīmīga vārdšķira vai kategorija' in gram['Flags']['Citi']:
                    result['pos'] = []
                if 'FlagText' in gram and db_connection_info['schema'] != 'tezaurs':
                    result['pos_text'] = gram['FlagText']
                if 'FreeText' in gram and db_connection_info['schema'] != 'tezaurs':
                    result['pos_text'] = gram['FreeText']
            if lexeme.data and 'Pronunciations' in lexeme.data:
                result['pronun'] = lexeme.data['Pronunciations']
            senses = fetch_senses(row.id)
            if senses:
                result['senses'] = senses
            yield result
        print(f'{counter}\r')


def fetch_lexeme(lexeme_id, entry_human_key):
    if not lexeme_id:
        print(f'No primary lexeme id for entry {entry_human_key}!')
        return
    lex_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    sql_primary_lex = f"""
SELECT l.id, lemma, paradigm_id, l.data, p.data as paradigm_data
FROM {db_connection_info['schema']}.lexemes l
LEFT OUTER JOIN {db_connection_info['schema']}.paradigms p ON l.paradigm_id = p.id
WHERE l.id = {lexeme_id}
"""
    lex_cursor.execute(sql_primary_lex)
    lexemes = lex_cursor.fetchall()
    if not lexemes or len(lexemes) < 1:
        print(f'No primary lexeme for entry {entry_human_key}!')
        return
    if len(lexemes) > 1:
        print(f'Too many primary lexemes for entry {entry_human_key}!')
    return lexemes[0]


def fetch_senses(entry_id, parent_sense_id=None):
    if not entry_id:
        return
    sense_cursor = connection.cursor(cursor_factory=NamedTupleCursor)
    parent_sense_clause = 'is NULL'
    if parent_sense_id:
        parent_sense_clause = f"""= {parent_sense_id}"""
    sql_senses = f"""
SELECT id, gloss, order_no, parent_sense_id FROM {db_connection_info['schema']}.senses
WHERE entry_id = {entry_id} and parent_sense_id {parent_sense_clause}
ORDER BY order_no
"""
    sense_cursor.execute(sql_senses)
    senses = sense_cursor.fetchall()
    if not senses:
        return
    result = []
    for sense in senses:
        # sense_data = json.loads(sense.data)
        subsenses = fetch_senses(entry_id, sense.id)
        sense_dict = {'ord': sense.order_no, 'gloss': sense.gloss}
        if subsenses:
            sense_dict['subsenses'] = subsenses
        result.append(sense_dict)
    return result


def dump_entries(filename):
    global schema
    with open(filename, 'w', encoding='utf8') as f:
        f.write('<TEI>\n')
        f.write('\t<teiHeader>TODO</teiHeader>\n')
        f.write('\t<body>\n')
        for entry in fetch_entries():
            if whitelist is not None and not whitelist.check(entry["lemma"], entry["hom_id"]):
                continue
            entry_id = f'{dbname}/{entry["id"]}'
            if (entry['hom_id'] > 0):
                f.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("hom")}>\n')
            elif (entry['lemma'] and 'pos' in entry and 'Vārda daļa' in entry['pos']):
                f.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("affix")}>\n')
            elif (entry['lemma'] and 'pos' in entry and 'Saīsinājums' in entry['pos']):
                f.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("abbr")}>\n')
            elif (entry['lemma'] and 'pos' in entry and 'Vārds svešvalodā' in entry['pos']):
                f.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("foreign")}>\n')
            else:
                f.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("main")}>\n')
            f.write('\t\t\t<form type="lemma">\n')
            f.write(f'\t\t\t\t<orth>{escape(entry["lemma"])}</orth>\n')
            if 'pronun' in entry:
                for pronun in entry['pronun']:
                    f.write(f'\t\t\t\t<pron>{escape(pronun)}</pron>\n')
            f.write('\t\t\t</form>\n')
            if 'pos' in entry or 'pos_text' in entry:
                f.write('\t\t\t<gramGrp>\n')
                if 'pos' in entry:
                    for g in entry['pos']:
                        f.write(f'\t\t\t\t<gram type="pos">{escape(g)}</gram>\n')
                    # f.write(f'\t\t\t\t\t<gram>{"; ".join(entry["pos"])}</gram>\n')
                elif 'pos_text' in entry:
                    f.write(f'\t\t\t\t<gram>{escape(entry["pos_text"])}</gram>\n')
                f.write('\t\t\t</gramGrp>\n')
            if 'senses' in entry:
                for sense in entry['senses']:
                    dump_sense(f, sense, '\t\t\t', f'{dbname}/{entry["id"]}')
            if 'etym' in entry:
                etym_text = escape(entry["etym"])
                etym_text = etym_text.replace('&lt;em&gt;', '<mentioned>').replace('&lt;/em&gt;', '</mentioned>')
                f.write(f'\t\t\t<etym>{etym_text}</etym>\n')
            f.write('\t\t</entry>\n')
        f.write('\t</body>')
        f.write('</TEI>\n')

def dump_sense(filestream, sense, indent, id_stub):
    sense_id = f'{id_stub}/{sense["ord"]}'
    sense_ord = f'{sense["ord"]}'
    filestream.write(f'{indent}<sense id={quoteattr(sense_id)} n={quoteattr(sense_ord)}>\n')
    gloss_text = escape(sense["gloss"]).replace('&lt;em&gt;', '<mentioned>').replace('&lt;/em&gt;', '</mentioned>')
    filestream.write(f'{indent}\t<def>{gloss_text}</def>\n')
    if 'subsenses' in sense:
        for subsense in sense['subsenses']:
            dump_sense(filestream, subsense, indent+'\t', sense_id)
    filestream.write(f'{indent}</sense>\n')


if len(sys.argv) > 1:
    dbname = sys.argv[1]
if len(sys.argv) > 2:
    whitelist = EntryWhitelist()
    whitelist.load(sys.argv[2])
    if len(whitelist.entries) < 1:
        whitelist = None
filename_infix = ""
if whitelist is not None:
    filename_infix = "_filtered"
db_connect()
filename = f'{db_connection_info["dbname"]}_tei{filename_infix}.xml'
dump_entries(filename)
print(f'Done! Output written to {filename}')
