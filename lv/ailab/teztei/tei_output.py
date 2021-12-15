from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

class TEI_Writer:
    def __init__(self, file, dict_id, whitelist=None):
        self.file = file
        self.dict_id = dict_id
        self.whitelist = whitelist

    def print_head(self):
        self.file.write('<TEI>\n')
        self.file.write('\t<teiHeader>TODO</teiHeader>\n')
        self.file.write('\t<body>\n')

    def print_tail(self):
        self.file.write('\t</body>')
        self.file.write('</TEI>\n')

    def print_entry(self, entry):
        if self.whitelist is not None and not self.whitelist.check(entry["lemma"], entry["hom_id"]):
            return
        entry_id = f'{self.dict_id}/{entry["id"]}'
        if (entry['hom_id'] > 0):
            self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("hom")}>\n')
        elif (entry['lemma'] and 'pos' in entry and 'Vārda daļa' in entry['pos']):
            self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("affix")}>\n')
        elif (entry['lemma'] and 'pos' in entry and 'Saīsinājums' in entry['pos']):
            self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("abbr")}>\n')
        elif (entry['lemma'] and 'pos' in entry and 'Vārds svešvalodā' in entry['pos']):
            self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("foreign")}>\n')
        else:
            self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("main")}>\n')
        self.file.write('\t\t\t<form type="lemma">\n')
        self.file.write(f'\t\t\t\t<orth>{escape(entry["lemma"])}</orth>\n')
        if 'pronun' in entry:
            for pronun in entry['pronun']:
                self.file.write(f'\t\t\t\t<pron>{escape(pronun)}</pron>\n')
        self.file.write('\t\t\t</form>\n')
        if 'pos' in entry or 'pos_text' in entry:
            self.file.write('\t\t\t<gramGrp>\n')
            if 'pos' in entry:
                for g in entry['pos']:
                    self.file.write(f'\t\t\t\t<gram type="pos">{escape(g)}</gram>\n')
                # self.file.write(f'\t\t\t\t\t<gram>{"; ".join(entry["pos"])}</gram>\n')
            elif 'pos_text' in entry:
                self.file.write(f'\t\t\t\t<gram>{escape(entry["pos_text"])}</gram>\n')
            self.file.write('\t\t\t</gramGrp>\n')
        if 'senses' in entry:
            for sense in entry['senses']:
                self.print_sense(sense, '\t\t\t', f'{self.dict_id}/{entry["id"]}')
        if 'etym' in entry:
            etym_text = escape(entry["etym"])
            etym_text = etym_text.replace('&lt;em&gt;', '<mentioned>').replace('&lt;/em&gt;', '</mentioned>')
            self.file.write(f'\t\t\t<etym>{etym_text}</etym>\n')
        self.file.write('\t\t</entry>\n')

    def print_sense(self, sense, indent, id_stub):
        sense_id = f'{id_stub}/{sense["ord"]}'
        sense_ord = f'{sense["ord"]}'
        self.file.write(f'{indent}<sense id={quoteattr(sense_id)} n={quoteattr(sense_ord)}>\n')
        gloss_text = escape(sense["gloss"]).replace('&lt;em&gt;', '<mentioned>').replace('&lt;/em&gt;', '</mentioned>')
        self.file.write(f'{indent}\t<def>{gloss_text}</def>\n')
        if 'subsenses' in sense:
            for subsense in sense['subsenses']:
                self.print_sense(subsense, indent + '\t', sense_id)
        self.file.write(f'{indent}</sense>\n')