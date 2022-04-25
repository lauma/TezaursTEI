import re
from pprint import pprint
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

    # TODO: sakārtot, lai drukā ar jauno leksēmu drukāšanas funkciju un visas leksēmas
    def print_entry(self, entry):
        #if self.whitelist is not None and not self.whitelist.check(entry['mainLexeme']['lemma'], entry['hom_id']):
        if self.whitelist is not None and not self.whitelist.check(entry['headword'], entry['hom_id']):
            return
        entry_id = f'{self.dict_id}/{entry["id"]}'
        entry_params = {'id': entry_id, 'sortKey': entry['headword']}
        main_lexeme = entry['lexemes'][0]
        if entry['hom_id'] > 0:
            entry_params['n'] = str(entry["hom_id"])
        if entry['type'] == 'mwe' or entry['type'] == 'MWE':
            entry_params['type'] = "mwe"
        elif main_lexeme['lemma'] and 'pos' in entry and 'Vārda daļa' in main_lexeme['pos'] or \
                entry['type'] == 'wordPart':
            entry_params['type'] = "affix" #FIXME
        elif main_lexeme['lemma'] and 'pos' in entry and 'Saīsinājums' in main_lexeme['pos'] or \
                'paradigm' in main_lexeme and main_lexeme['paradigm']['id'] == 'abbr':
            entry_params['type'] = "abbr"
        elif main_lexeme['lemma'] and 'pos' in entry and 'Vārds svešvalodā' in main_lexeme['pos'] or \
                'paradigm' in main_lexeme and main_lexeme['paradigm']['id'] == 'foreign':
            entry_params['type'] = "foreign"
        else:
            entry_params['type'] = "main"
        self._start_node('entry', entry_params)
        #FIXME homonīmi
        #self.print_lexeme(entry['mainLexeme'], entry['headword'], True)
        is_first = True
        for lexeme in entry['lexemes']:
            self.print_lexeme(lexeme, entry['headword'], entry['type'], is_first)
            is_first = False
        if 'senses' in entry:
            for sense in entry['senses']:
                self.print_sense(sense, f'{self.dict_id}/{entry["id"]}')
        if 'etym' in entry:
            self._do_leaf_node('etym', {}, entry['etym'], True)
        self._end_node('entry')

    def print_lexeme(self, lexeme, headword, entry_type, is_main=False):
        
        if is_main:
            self._start_node('form', {'type': 'lemma'})
        else:
            self._start_node('form', {'type': TEI_Writer.lexeme_type(lexeme['type'], entry_type)})

        # TODO vai šito vajag?
        if is_main and lexeme['lemma'] != headword:
            self._do_leaf_node('form', {'type': 'headword'}, headword)
        self._do_leaf_node('orth', {'type': 'lemma'}, lexeme['lemma'])
        if 'pronun' in lexeme:
            for pronun in lexeme['pronun']:
                self._do_leaf_node('pron', {}, pronun)

        self.print_gram(lexeme)
        self._end_node('form')

    def print_gram(self, parent):
        #if 'pos' not in parent and 'flags' not in parent and 'struct_restr' not in parent and \
        if 'flags' not in parent and 'struct_restr' not in parent and \
                'free_text' not in parent and 'infl_text' not in parent:
            return

        self._start_node('gramGrp', {})
        #TODO vai šito vajag?
        #if 'pos' in lexeme or 'pos_text' in lexeme:
        #    if 'pos' in lexeme:
        #        for g in set(lexeme['pos']):
        #            self._do_leaf_node('gram', {'type': 'pos'}, g)
        #    elif 'pos_text' in lexeme:
        #        self._do_leaf_node('gram', {}, lexeme['pos_text'])

        # TODO: kā labāk - celms kā karogs vai paradigmas daļa?
        if 'paradigm' in parent:
            paradigm_text = parent['paradigm']['id']

            if 'stem_inf' in parent['paradigm'] or 'stem_pres' in parent['paradigm'] or 'stem_past' in parent['paradigm']:
                paradigm_text = paradigm_text + ':'
                if 'stem_inf' in parent['paradigm']:
                    paradigm_text = paradigm_text + parent['paradigm']['stem_inf'] + ';'
                else:
                    paradigm_text = paradigm_text + ';'
                if 'stem_pres' in parent['paradigm']:
                    paradigm_text = paradigm_text + parent['paradigm']['stem_pres'] + ';'
                else:
                    paradigm_text = paradigm_text + ';'
                if 'stem_past' in parent['paradigm']:
                    paradigm_text = paradigm_text + parent['paradigm']['stem_past']

            self._do_leaf_node('iType', {'type': 'https://github.com/PeterisP/morphology'}, paradigm_text)
        elif 'infl_text' in parent:
            self._do_leaf_node('iType', {}, parent['infl_text'])

        if 'flags' in parent:
            self.print_flags(parent['flags'])
        if 'struct_restr' in parent:
            self.print_struct_restr(parent['struct_restr'])
        if not ('flags' in parent) and not ('struct_restr' in parent) and 'free_text' in parent:
            self._do_leaf_node('gram', {}, parent['free_text'])

        self._end_node('gramGrp')

    # TODO piesaistīt karoga anglisko nosaukumu
    def print_flags (self, flags):
        if not flags:
            return
        self._start_node('gramGrp', {'type': 'properties'})
        for key in sorted(flags.keys()):
            if isinstance(flags[key], list):
                for value in flags[key]:
                    self._do_leaf_node('gram', {'type': key}, value)
            else:
                self._do_leaf_node('gram', {'type': key}, flags[key])
        self._end_node('gramGrp')

    # TODO piesaistīt ierobežojuma anglisko nosaukumu un varbūt arī biežuma?
    def print_struct_restr (self, struct_restr):
        if 'OR' in struct_restr:
            self._start_node('gramGrp', {'type': 'restrictionDisjunction'})
            for restr in struct_restr['OR']:
                self.print_struct_restr(restr)
            self._end_node('gramGrp')
        elif 'AND' in struct_restr:
            self._start_node('gramGrp', {'type': 'restrictionConjunction'})
            for restr in struct_restr['AND']:
                self.print_struct_restr(restr)
            self._end_node('gramGrp')
        else:
            gramGrpParams = {'type': struct_restr['Restriction']}
            if 'Frequency' in struct_restr:
                gramGrpParams['subtype'] = struct_restr['Frequency']
            self._start_node('gramGrp', gramGrpParams) #TODO piesaistīt anglisko nosaukumu
            if 'Value' in struct_restr and 'Flags' in struct_restr['Value']:
                self.print_flags(struct_restr['Value']['Flags'])
            if 'Value' in struct_restr and 'LanguageMaterial' in struct_restr['Value']:
                for material in struct_restr['Value']['LanguageMaterial']:
                    self._do_leaf_node('gram', {'type': 'languageMaterial'}, material)
            self._end_node('gramGrp')

    def lexeme_type (type_from_db, entry_type):
        match type_from_db:
            case 'default':
                if (entry_type == 'word'):
                    return 'simple'
                elif (entry_type == 'mwe'):
                    return 'phrase'
                else:
                    return 'affix'
            case 'derivative':
                return 'derivative'
            case 'alternativeSpelling':
                return 'variant'
            case 'findVia':
                return 'other'
            case 'abbreviation':
                return 'abbreviation'
            case 'alternativeSpellingDerivative':
                return 'variantDerivative'

    def print_sense(self, sense, id_stub):
        sense_id = f'{id_stub}/{sense["ord"]}'
        sense_ord = f'{sense["ord"]}'
        self._start_node('sense', {'id': sense_id, 'n': sense_ord})
        self.print_gram(sense)
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
                self._start_node('xr', {'type': 'gradation_class'})
                self._do_leaf_node('ref', {}, f'{self.dict_id}/synset:{gradset["gradset_cat"]}')
                self._end_node('xr')
