import regex

from lv.ailab.dictutils.gloss_normalization import mandatory_normalization, full_cleanup
from lv.ailab.dictutils.pron_normalization import prettify_pronunciation, prettify_text_with_pronunciation
from lv.ailab.tezdb.query_uttils import extract_paradigm_text
from lv.ailab.xmlutils.writer import XMLWriter


class TEIWriter(XMLWriter):
    dict_version = 0

    def __init__(self, file, dict_version, whitelist=None):
        super().__init__(file, "  ", "\n")
        self.whitelist = whitelist
        self.debug_entry_id = ''
        self.dict_version = dict_version

    def _do_leaf_node(self, name, attrs, content, mentions=False, ge_links=None, gs_links=None):
        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.startElement(name, attrs)
        if mentions:
            self._do_content_with_mentions_glosslinks(content, ge_links, gs_links)
        else:
            self.gen.characters(content)
        self.gen.endElement(name)
        self.gen.ignorableWhitespace(self.newline_chars)

    def _do_content_with_mentions_glosslinks(self, content, ge_links=None, gs_links=None):
        # parts = regex.split('</?(?:em|i)>', content)
        underscore_count = len(regex.findall(r'(?<!\\)_', content))
        if underscore_count % 2 > 0:
            print(f'Odd number of _ in entry {self.debug_entry_id}, string {content}!\n')
        parts = regex.split(r'(?<!\\)_+', content)
        is_mentioned = False
        # if regex.search('^</?(?:em|i)>', content):
        if regex.search(r'^_+', content):
            parts.pop(0)
            is_mentioned = True
        for part in parts:
            if is_mentioned:
                self.gen.startElement('mentioned', {})
                self._do_content_with_glosslinks(part, ge_links, gs_links)
                self.gen.endElement('mentioned')
                is_mentioned = False
            else:
                self._do_content_with_glosslinks(part, ge_links, gs_links)
                is_mentioned = True

    def _do_content_with_glosslinks(self, content, ge_links=None, gs_links=None):
        if not ge_links and not gs_links:
            self.gen.characters(full_cleanup(content))
        else:
            content_left = content
            glosslink_regex = r'(.*?)\[((?:\p{L}\p{M}*)+)\]\{([sen]):(\d+)\}(.*)'
            match = regex.fullmatch(glosslink_regex, content_left)
            while match:
                self.gen.characters(match.group(1))
                word = match.group(2)
                content_left = match.group(5)
                link_type = match.group(3)
                link_id = int(match.group(4))
                link_ref = None
                if link_type == 'e':
                    if not ge_links.get(link_id):
                        print(
                            f'Invalid gloss link {link_type}:{link_id} in entry {self.debug_entry_id}'
                            + f' (available links {ge_links}).\n')
                    link_ref = ge_links[link_id]
                elif link_type == 's':
                    if not gs_links.get(link_id):
                        print(
                            f'Invalid gloss link {link_type}:{link_id} in entry {self.debug_entry_id}'
                            + f' (available links {gs_links}).\n')
                    link_ref = gs_links[link_id]['softid']
                else:
                    print(f'Empty gloss link {link_type}:{link_id} in entry {self.debug_entry_id}\n')
                if link_ref:
                    self.gen.startElement('ref',
                                          {'target': f'{self.dict_version}/{link_ref}', 'type': 'disambiguation'})
                    self.gen.characters(word)
                    self.gen.endElement('ref')
                else:
                    self.gen.characters(word)
                match = regex.fullmatch(glosslink_regex, content_left)
            self.gen.characters(content_left)

    def print_head(self, dictionary, title_long = 'Dictionary',
                   edition='TODO', editors='TODO',
                   entry_count='TODO', lexeme_count='TODO', sense_count='TODO',
                   year='TODO', month='TODO', url=None, copyright=None):
        self.start_document()
        self.start_node('TEI', {})
        self.start_node('fileDesc', {})

        self.start_node('titleStmt', {})
        self._do_leaf_node('title', {}, title_long)

        if dictionary == 'tezaurs' or dictionary == 'mlvv' or dictionary == 'llvv':
            self._do_leaf_node('editor', {}, editors)
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
        self._do_leaf_node('date', {}, f"{year}-{month:02}")
        if dictionary == 'tezaurs' or dictionary == 'llvv':
            self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
            self.gen.startElement('publisher', {})
            self.gen.startElement('ref', {'target': 'https://ailab.lv'})
            self.gen.characters('AI Lab')
            self.gen.endElement('ref')
            self.gen.characters(' at Institute of Mathematics and Computer Science, University of Latvia')
            self.gen.endElement('publisher')
            self.gen.ignorableWhitespace(self.newline_chars)

        if dictionary == 'mlvv' or dictionary == 'llvv':
            self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
            self.gen.startElement('publisher', {})
            self.gen.startElement('ref', {'target': 'https://lavi.lu.lv/'})
            self.gen.characters('LII')
            self.gen.endElement('ref')
            self.gen.characters(' at University of Latvia')
            self.gen.endElement('publisher')
            self.gen.ignorableWhitespace(self.newline_chars)

        if dictionary == 'tezaurs' or dictionary == 'mlvv' or dictionary == 'llvv':
            self.start_node('availability', {'status': 'free'})

            if url is not None and (dictionary == 'tezaurs' or dictionary == 'mlvv' or dictionary == 'llvv'):
                self.do_simple_leaf_node('p', {}, copyright)

            self.do_simple_leaf_node('licence', {'target': 'https://creativecommons.org/licenses/by-sa/4.0/'},
                                     'Creative Commons Attribution-ShareAlike 4.0 International License')
            self.end_node('availability')
        if url is not None and (dictionary == 'tezaurs' or dictionary == 'mlvv' or dictionary == 'llvv'):
            self.do_simple_leaf_node('ptr', {'target': url})
        self.end_node('publicationStmt')

        if dictionary == 'llvv':
            self.start_node('sourceDesc', {})
            self.start_node('biblStruct', {})
            self.start_node('monogr', {})
            self.do_simple_leaf_node('title', {}, 'Latviešu literārās valodas vārdnīca')
            self.do_simple_leaf_node('editor', {}, 'Laimdots Ceplītis')
            self.do_simple_leaf_node('title', {}, 'Latviešu literārās valodas vārdnīca')
            self.start_node('imprint', {})
            self.do_simple_leaf_node('publisher', {}, 'Izdevniecība "Zinātne"')
            self.do_simple_leaf_node('pubPlace', {}, 'Rīga')
            self.do_simple_leaf_node('date', {}, '1972-1996')
            self.end_node('imprint')
            self.end_node('monogr')
            self.end_node('biblStruct')
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
            # FIXME būtu labi, ja te varētu gudrāk dalīt elementos.
            title = regex.sub('</?(?:em|i)>', '', source['title'])
            if 'url' in source and source['url']:
                self.do_simple_leaf_node('bibl', {'id': source['abbr'], 'url': source['url']}, title)
            else:
                self.do_simple_leaf_node('bibl', {'id': source['abbr']}, title)
        self.do_simple_leaf_node('bibl', {'id': 'MORPHO', 'url': 'https://github.com/PeterisP/morphology'},
                                 'Paikens P. Morphological Analyzer and Synthesizer for Latvian. ' +
                                 'Institute of Mathematics and Computer Science, University of Latvia, 2005-2022.')
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
        if 'examples' in entry:
            for example in entry['examples']:
                self.print_example(example)
        if 'etym' in entry:
            self._do_leaf_node('etym', {}, mandatory_normalization(entry['etym']), True)
        if 'sources' in entry:
            self.print_esl_sources(entry['sources'])
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
                self._do_leaf_node('pron', {}, prettify_pronunciation(pronun))

        self.print_gram(lexeme)

        if 'sources' in lexeme:
            self.print_esl_sources(lexeme['sources'])

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

            self._do_leaf_node('iType', {'type': 'computational', 'corresp': '#MORPHO'}, paradigm_text)
        elif 'infl_text' in parent:
            self._do_leaf_node('iType', {}, prettify_text_with_pronunciation(parent['infl_text']))

        if 'flags' in parent:
            self.print_flags(parent['flags'])
        if 'struct_restr' in parent:
            self.print_struct_restr(parent['struct_restr'])
        if not ('flags' in parent) and not ('struct_restr' in parent) and 'free_text' in parent:
            self._do_leaf_node('gram', {}, prettify_text_with_pronunciation(parent['free_text']))

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
        norm_gloss = mandatory_normalization(sense['gloss'])
        self._do_leaf_node('def', {}, norm_gloss, True, sense.get('ge_links'), sense.get('gs_links'))  # Jo var būt None
        if 'synset_id' in sense:  # and 'synset_senses' in sense:

            self.print_synset_related(sense['synset_id'], sense['synset_senses'], sense['synset_rels'],
                                      sense['gradset'])
        if 'examples' in sense:
            for example in sense['examples']:
                self.print_example(example)

        if 'sources' in sense:
            self.print_esl_sources(sense['sources'])

        if 'subsenses' in sense:
            for subsense in sense['subsenses']:
                self.print_sense(subsense, sense_id)

        self.end_node('sense')

    def print_example(self, example):
        if 'text' not in example or not example['text']:
            return
        self.start_node('cit', {'type': 'example'})

        if 'location' not in example:
            self._do_leaf_node('quote', {}, example['text'])
        else:
            self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
            self.gen.startElement('quote', {})
            self.gen.characters(example['text'][:example['location']+0])
            self.gen.startElement('anchor', {})
            self.gen.endElement('anchor')
            self.gen.characters(example['text'][example['location']+0:])
            self.gen.endElement('quote')
            self.gen.ignorableWhitespace(self.newline_chars)

        if 'source' in example:
            self._do_leaf_node('bibl', {}, example['source'])

        self.end_node('cit')

    def print_esl_sources(self, sources):
        if not sources:
            return
        self.start_node('listBibl', {})
        for source in sources:
            if source['details']:
                self.start_node('bibl', {'corresp': f"#{source['abbr']}"})
                self.do_simple_leaf_node('biblScope', {}, source['details'])
                self.end_node('bibl')
            else:
                self.do_simple_leaf_node('bibl', {'corresp': f"#{source['abbr']}"})
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
