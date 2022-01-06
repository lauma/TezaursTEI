import re
from xml.sax.saxutils import XMLGenerator

indent_char = "  "
newline_char = "\n"

class TEI_Writer:
    def __init__(self, file, dict_id, whitelist=None):
        self.file = file
        self.dict_id = dict_id
        self.whitelist = whitelist
        self.gen = XMLGenerator(file, 'UTF-8', True)
        self.xml_depth = 0

    def _start_node(self, name, attrs):
        global indent_char
        global newline_char
        self.gen.ignorableWhitespace(indent_char*self.xml_depth)
        self.gen.startElement(name, attrs)
        self.gen.ignorableWhitespace(newline_char)
        self.xml_depth = self.xml_depth + 1

    def _end_node(self, name):
        global indent_char
        global newline_char
        self.xml_depth = self.xml_depth - 1
        self.gen.ignorableWhitespace(indent_char*self.xml_depth)
        self.gen.endElement(name)
        self.gen.ignorableWhitespace(newline_char)

    def _do_leaf_node(self, name, attrs, content, mentions=False):
        global indent_char
        global newline_char
        self.gen.ignorableWhitespace(indent_char * self.xml_depth)
        self.gen.startElement(name, attrs)
        if mentions:
            self._do_content_with_mentions(content)
        else:
            self.gen.characters(content)
        self.gen.endElement(name)
        self.gen.ignorableWhitespace(newline_char)

    def _do_content_with_mentions(self, content):
        parts = re.split('</?(?:em|i)>', content)
        is_mentioned = False
        if re.match('^</?(?:em|i)>', content):
            is_mentioned = True
            self.gen.startElement('mentioned', {})
        self.gen.characters(parts.pop(0))
        for part in parts:
            if is_mentioned:
                self.gen.endElement('mentioned')
                is_mentioned = False
            else:
                self.gen.startElement('mentioned', {})
                is_mentioned = True
            self.gen.characters(part)
        if is_mentioned:
            self.gen.endElement(is_mentioned)

    def print_head(self):
        self.gen.startDocument()
        self._start_node('TEI', {})
        self._do_leaf_node('teiHeader', {}, 'TODO')
        self._start_node('body', {})

    def print_tail(self):
        self._end_node('body')
        self._end_node('TEI')
        self.gen.endDocument()

    def print_entry(self, entry):
        if self.whitelist is not None and not self.whitelist.check(entry["lemma"], entry["hom_id"]):
            return
        entry_id = f'{self.dict_id}/{entry["id"]}'
        self._start_node('entry', {'id': entry_id})
        #FIXME homonīmi un tipi
        #if (entry['hom_id'] > 0):
        #    self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("hom")}>\n')
        #elif (entry['lemma'] and 'pos' in entry and 'Vārda daļa' in entry['pos']):
        #    self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("affix")}>\n')
        #elif (entry['lemma'] and 'pos' in entry and 'Saīsinājums' in entry['pos']):
        #    self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("abbr")}>\n')
        #elif (entry['lemma'] and 'pos' in entry and 'Vārds svešvalodā' in entry['pos']):
        #    self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("foreign")}>\n')
        #else:
        #    self.file.write(f'\t\t<entry id={quoteattr(entry_id)} type={quoteattr("main")}>\n')
        self._start_node('form', {'type': 'lemma'})
        self._do_leaf_node('orth', {}, entry['lemma'])
        if 'pronun' in entry:
            for pronun in entry['pronun']:
                self._do_leaf_node('pron', {}, pronun)
        self._end_node('form')
        if 'pos' in entry or 'pos_text' in entry:
            self._start_node('gramGrp', {})
            if 'pos' in entry:
                for g in set(entry['pos']):
                    self._do_leaf_node('gram', {'type': 'pos'}, g)
            elif 'pos_text' in entry:
                self._do_leaf_node('gram', {}, entry['pos_text'])
            self._end_node('gramGrp')
        if 'senses' in entry:
            for sense in entry['senses']:
                self.print_sense(sense, f'{self.dict_id}/{entry["id"]}')
        if 'etym' in entry:
            self._do_leaf_node('etym', {}, entry['etym'], True)
        self._end_node('entry')

    def print_sense(self, sense, id_stub):
        sense_id = f'{id_stub}/{sense["ord"]}'
        sense_ord = f'{sense["ord"]}'
        self._start_node('sense', {'id': sense_id, 'n': sense_ord})
        self._do_leaf_node('def', {}, sense['gloss'], True)
        if 'synset_id' in sense:# and 'synset_senses' in sense:

            self.print_synset_related(sense['synset_id'], sense['synset_senses'], sense['synset_rels'],
                                      sense['gradset'])
        if 'subsenses' in sense:
            for subsense in sense['subsenses']:
                self.print_sense(subsense, sense_id)
        self._end_node('sense')

    def print_synset_related(self, synset_id, synset_senses, synset_rels, gradset):
        if synset_senses:
            self._start_node('xr', {'type': 'synset', 'id': f'{self.dict_id}/synset:{synset_id}'})
            for synset_sense in synset_senses:
                # TODO use hard ids when those are fixed
                self._do_leaf_node('ref', {}, f'{self.dict_id}/{synset_sense["softid"]}')
            self._end_node('xr')
        if synset_rels:
            for synset_rel in synset_rels:
                self._start_node('xr', {'type': f'{synset_rel["other_name"]}'})
                self._do_leaf_node('ref', {}, f'{self.dict_id}/synset:{synset_rel["other"]}')
                self._end_node('xr')
        if gradset:
            self._start_node('xr', {'type': 'gradation_set', 'id': f'{self.dict_id}/gradset:{gradset["gradset_id"]}'})
            for synset in gradset['member_synsets']:
                self._do_leaf_node('ref', {}, f'{self.dict_id}/synset:{synset}')
            self._end_node('xr')
            if gradset['gradset_cat']:
                self._start_node('xr', {'type': 'gradation_set_category'})
                self._do_leaf_node('ref', {}, f'{self.dict_id}/synset:{gradset["gradset_cat"]}')
                self._end_node('xr')
