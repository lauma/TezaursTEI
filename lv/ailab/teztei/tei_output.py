import re

from lv.ailab.tezdb.query_uttils import extract_paradigm_text
from lv.ailab.xmlutils.writer import XMLWriter


class TEIWriter(XMLWriter):
    dict_version = 0

    def __init__(self, file, dict_version, whitelist=None):
        super().__init__(file, "  ", "\n")
        self.whitelist = whitelist
        self.debug_entry_id = ''
        self.dict_version = dict_version

    def _do_leaf_node(self, name, attrs, content, mentions=False):
        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.startElement(name, attrs)
        if mentions:
            self._do_content_with_mentions(content)
        else:
            self.gen.characters(content)
        self.gen.endElement(name)
        self.gen.ignorableWhitespace(self.newline_chars)

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
            self.gen.endElement('mentioned')

    def print_head(self, edition='TODO', entry_count='TODO', lexeme_count='TODO', sense_count='TODO', year='TODO'):
        self.start_document()
        self.start_node('TEI', {})
        self.start_node('fileDesc', {})
        self.start_node('titleStmt', {})
        self._do_leaf_node('title', {}, 'Tēzaurs.lv - dictionary and thesaurus of Latvian')
        self._do_leaf_node('editor', {}, 'Andrejs Spektors et al.')
        self.end_node('titleStmt')
        self.start_node('editionStmt', {})
        self._do_leaf_node('edition', {}, edition)
        self.end_node('editionStmt')
        self.start_node('extent', {})
        self._do_leaf_node('measure', {'unit': 'entry', 'quantity': entry_count}, None)
        self._do_leaf_node('measure', {'unit': 'lexeme', 'quantity': lexeme_count}, None)
        self._do_leaf_node('measure', {'unit': 'sense', 'quantity': sense_count}, None)
        self.end_node('extent')
        self.start_node('publicationStmt', {})
        self._do_leaf_node('publisher', {},
                           'AI Lab at the Institute of Mathematics and Computer Science, University of Latvia')
        self.start_node('availability', {'status': 'free'})

        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.startElement('p', {})
        self.gen.characters(f'Copyright (C) 2009-{year} by ')
        self.gen.startElement('ref', {'target': 'http://ailab.lv/'})
        self.gen.characters('AI Lab')
        self.gen.endElement('ref')
        self.gen.characters(', IMCS, UL.')
        self.gen.endElement('p')
        self.gen.ignorableWhitespace(self.newline_chars)

        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.startElement('p', {})
        self.gen.characters('Available under ')
        self.gen.startElement('ref', {'target': 'https://creativecommons.org/licenses/by-sa/4.0/'})
        self.gen.characters('Creative Commons Attribution-ShareAlike 4.0 International License')
        self.gen.endElement('ref')
        self.gen.characters('.')
        self.gen.endElement('p')
        self.gen.ignorableWhitespace(self.newline_chars)

        self.end_node('availability')
        self.end_node('publicationStmt')
        self.start_node('sourceDesc', {})
        self._do_leaf_node('p', {'ref': 'https://tezaurs.lv/'}, 'Tezaurs.lv')
        self.end_node('sourceDesc')
        self.end_node('fileDesc')

        self.start_node('body', {})

    def print_tail(self):
        self.end_node('body')
        self.end_node('TEI')
        self.end_document()

    def print_back_matter(self, sources):
        self.start_node('back', {})
        self.start_node('listBibl', {})
        for source in sources:
            if 'url' in source and source['url']:
                self._do_leaf_node('bibl', {'id': source['abbr'], 'url': source['url']}, source['title'], True)
            else:
                self._do_leaf_node('bibl', {'id': source['abbr']}, source['title'], True)
        self.end_node('listBibl')
        self.end_node('back')

    # TODO: sakārtot, lai drukā ar jauno leksēmu drukāšanas funkciju un visas leksēmas
    def print_entry(self, entry):
        # if self.whitelist is not None and not self.whitelist.check(entry['mainLexeme']['lemma'], entry['hom_id']):
        if self.whitelist is not None and not self.whitelist.check(entry['headword'], entry['hom_id']):
            return
        self.debug_entry_id = entry['id']
        entry_id = f'{self.dict_version}/{entry["id"]}'
        entry_params = {'id': entry_id, 'sortKey': entry['headword']}
        main_lexeme = entry['lexemes'][0]
        if entry['hom_id'] > 0:
            entry_params['n'] = str(entry["hom_id"])
        if entry['type'] == 'mwe' or entry['type'] == 'MWE':
            entry_params['type'] = "mwe"
        elif main_lexeme['lemma'] and 'pos' in entry and 'Vārda daļa' in main_lexeme['pos'] or \
                entry['type'] == 'wordPart':
            entry_params['type'] = "affix"  # FIXME
        elif main_lexeme['lemma'] and 'pos' in entry and 'Saīsinājums' in main_lexeme['pos'] or \
                'paradigm' in main_lexeme and main_lexeme['paradigm']['id'] == 'abbr':
            entry_params['type'] = "abbr"
        elif main_lexeme['lemma'] and 'pos' in entry and 'Vārds svešvalodā' in main_lexeme['pos'] or \
                'paradigm' in main_lexeme and main_lexeme['paradigm']['id'] == 'foreign':
            entry_params['type'] = "foreign"
        else:
            entry_params['type'] = "main"
        self.start_node('entry', entry_params)
        # FIXME homonīmi
        # self.print_lexeme(entry['mainLexeme'], entry['headword'], True)
        is_first = True
        self.print_gram(entry)
        for lexeme in entry['lexemes']:
            self.print_lexeme(lexeme, entry['headword'], entry['type'], is_first)
            is_first = False
        if 'senses' in entry:
            for sense in entry['senses']:
                self.print_sense(sense, f'{self.dict_version}/{entry["id"]}')
        if 'sources' in entry:
            self.print_sources(entry['sources'])
        if 'etym' in entry:
            self._do_leaf_node('etym', {}, entry['etym'], True)
        self.end_node('entry')

    def print_lexeme(self, lexeme, headword, entry_type, is_main=False):
        if is_main:
            self.start_node('form', {'type': 'lemma'})
        else:
            self.start_node('form', {'type': lexeme_type(lexeme['type'], entry_type)})

        # TODO vai šito vajag?
        if is_main and lexeme['lemma'] != headword:
            self._do_leaf_node('form', {'type': 'headword'}, headword)
        self._do_leaf_node('orth', {'type': 'lemma'}, lexeme['lemma'])
        if 'pronun' in lexeme:
            for pronun in lexeme['pronun']:
                self._do_leaf_node('pron', {}, pronun)

        self.print_gram(lexeme)
        self.end_node('form')

    def print_gram(self, parent):
        # if 'pos' not in parent and 'flags' not in parent and 'struct_restr' not in parent and \
        if 'flags' not in parent and 'struct_restr' not in parent and \
                'free_text' not in parent and 'infl_text' not in parent:
            return

        self.start_node('gramGrp', {})
        # TODO vai šito vajag?
        # if 'pos' in lexeme or 'pos_text' in lexeme:
        #    if 'pos' in lexeme:
        #        for g in set(lexeme['pos']):
        #            self._do_leaf_node('gram', {'type': 'pos'}, g)
        #    elif 'pos_text' in lexeme:
        #        self._do_leaf_node('gram', {}, lexeme['pos_text'])

        # TODO: kā labāk - celms kā karogs vai paradigmas daļa?
        if 'paradigm' in parent:
            paradigm_text = extract_paradigm_text(parent['paradigm'])
            # paradigm_text = parent['paradigm']['id']
            # if 'stem_inf' in parent['paradigm'] or 'stem_pres' in parent['paradigm'] \
            #        or 'stem_past' in parent['paradigm']:
            #    paradigm_text = paradigm_text + ':'
            #    if 'stem_inf' in parent['paradigm']:
            #        paradigm_text = paradigm_text + parent['paradigm']['stem_inf'] + ';'
            #    else:
            #        paradigm_text = paradigm_text + ';'
            #    if 'stem_pres' in parent['paradigm']:
            #        paradigm_text = paradigm_text + parent['paradigm']['stem_pres'] + ';'
            #    else:
            #        paradigm_text = paradigm_text + ';'
            #    if 'stem_past' in parent['paradigm']:
            #        paradigm_text = paradigm_text + parent['paradigm']['stem_past']

            self._do_leaf_node('iType', {'type': 'https://github.com/PeterisP/morphology'}, paradigm_text)
        elif 'infl_text' in parent:
            self._do_leaf_node('iType', {}, parent['infl_text'])

        if 'flags' in parent:
            self.print_flags(parent['flags'])
        if 'struct_restr' in parent:
            self.print_struct_restr(parent['struct_restr'])
        if not ('flags' in parent) and not ('struct_restr' in parent) and 'free_text' in parent:
            self._do_leaf_node('gram', {}, parent['free_text'])

        self.end_node('gramGrp')

    # TODO piesaistīt karoga anglisko nosaukumu
    def print_flags(self, flags):
        if not flags:
            return
        self.start_node('gramGrp', {'type': 'properties'})
        for key in sorted(flags.keys()):
            if isinstance(flags[key], list):
                for value in flags[key]:
                    self._do_leaf_node('gram', {'type': key}, value)
            else:
                self._do_leaf_node('gram', {'type': key}, flags[key])
        self.end_node('gramGrp')

    # TODO piesaistīt ierobežojuma anglisko nosaukumu un varbūt arī biežuma?
    def print_struct_restr(self, struct_restr):
        if 'OR' in struct_restr:
            self.start_node('gramGrp', {'type': 'restrictionDisjunction'})
            for restr in struct_restr['OR']:
                self.print_struct_restr(restr)
            self.end_node('gramGrp')
        elif 'AND' in struct_restr:
            self.start_node('gramGrp', {'type': 'restrictionConjunction'})
            for restr in struct_restr['AND']:
                self.print_struct_restr(restr)
            self.end_node('gramGrp')
        else:
            # if 'Restriction' not in struct_restr:
            #    print ("SAAD" + self.debug_entry_id)
            gramGrp_params = {'type': struct_restr['Restriction']}
            if 'Frequency' in struct_restr:
                gramGrp_params['subtype'] = struct_restr['Frequency']
            self.start_node('gramGrp', gramGrp_params)  # TODO piesaistīt anglisko nosaukumu
            if 'Value' in struct_restr and 'Flags' in struct_restr['Value']:
                self.print_flags(struct_restr['Value']['Flags'])
            if 'Value' in struct_restr and 'LanguageMaterial' in struct_restr['Value']:
                for material in struct_restr['Value']['LanguageMaterial']:
                    self._do_leaf_node('gram', {'type': 'languageMaterial'}, material)
            self.end_node('gramGrp')

    def print_sense(self, sense, id_stub):
        sense_id = f'{id_stub}/{sense["ord"]}'
        sense_ord = f'{sense["ord"]}'
        self.start_node('sense', {'id': sense_id, 'n': sense_ord})
        self.print_gram(sense)
        self._do_leaf_node('def', {}, sense['gloss'], True)
        if 'synset_id' in sense:  # and 'synset_senses' in sense:

            self.print_synset_related(sense['synset_id'], sense['synset_senses'], sense['synset_rels'],
                                      sense['gradset'])
        if 'subsenses' in sense:
            for subsense in sense['subsenses']:
                self.print_sense(subsense, sense_id)
        self.end_node('sense')

    def print_sources(self, sources):
        if not sources:
            return
        self.start_node('listBibl', {})
        for source in sources:
            if source['details']:
                self.start_node('bibl', {'corresp': source['abbr']})
                self.do_simple_leaf_node('biblScope', {}, source['details'])
                self.end_node('bibl')
            else:
                self.do_simple_leaf_node('bibl', {'corresp': source['abbr']})
        self.end_node('listBibl')

    def print_synset_related(self, synset_id, synset_senses, synset_rels, gradset):
        if synset_senses:
            self.start_node('xr', {'type': 'synset', 'id': f'{self.dict_version}/synset:{synset_id}'})
            for synset_sense in synset_senses:
                # TODO use hard ids when those are fixed
                self._do_leaf_node('ref', {}, f'{self.dict_version}/{synset_sense["softid"]}')
            self.end_node('xr')
        if synset_rels:
            for synset_rel in synset_rels:
                self.start_node('xr', {'type': f'{synset_rel["other_name"]}'})
                self._do_leaf_node('ref', {}, f'{self.dict_version}/synset:{synset_rel["other"]}')
                self.end_node('xr')
        if gradset:
            self.start_node('xr',
                            {'type': 'gradation_set', 'id': f'{self.dict_version}/gradset:{gradset["gradset_id"]}'})
            for synset in gradset['member_synsets']:
                self._do_leaf_node('ref', {}, f'{self.dict_version}/synset:{synset}')
            self.end_node('xr')
            if gradset['gradset_cat']:
                self.start_node('xr', {'type': 'gradation_class'})
                self._do_leaf_node('ref', {}, f'{self.dict_version}/synset:{gradset["gradset_cat"]}')
                self.end_node('xr')


def lexeme_type(type_from_db, entry_type):
    match type_from_db:
        case 'default':
            if entry_type == 'word':
                return 'simple'
            elif entry_type == 'mwe':
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
