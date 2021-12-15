#!/usr/bin/env python3
from lv.ailab.teztei.querries import fetch_entries
from lv.ailab.teztei.whitelist import EntryWhitelist
from lv.ailab.teztei.db_config import db_connection_info

import psycopg2
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


def dump_entries(filename):
    global schema
    with open(filename, 'w', encoding='utf8') as f:
        f.write('<TEI>\n')
        f.write('\t<teiHeader>TODO</teiHeader>\n')
        f.write('\t<body>\n')
        for entry in fetch_entries(connection, omit_pot_wordparts):
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
