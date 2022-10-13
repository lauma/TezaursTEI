from lv.ailab.xmlutils.writer import XMLWriter


class LMFWriter(XMLWriter):
    debug_id = 0
    wordnet_id = 0

    def __init__(self, file, dict_id,  wordnet_id):
        super().__init__(file, dict_id, "  ", "\n")
        self.wordnet_id = wordnet_id

    def print_head(self, wordnet_vers):
        self.start_document('<!DOCTYPE LexicalResource SYSTEM "http://globalwordnet.github.io/schemas/WN-LMF-1.1.dtd">')
        self.start_node('LexicalResource', {'xmlns:dc': "http://purl.org/dc/elements/1.1/"})
        self.start_node('Lexicon', {'id': self.wordnet_id,
                                    'label': 'Latvian Wordnet',
                                    'language': 'lv',
                                    'email': 'peteris@ailab.lv',
                                    'licence': 'https://creativecommons.org/licenses/by-nc/4.0/',
                                    'version': wordnet_vers,
                                    'url': 'https://wordnet.ailab.lv/',
                                    'citations': 'TODO',
                                    'logo': 'https://wordnet.ailab.lv/images/mazais-logo-ailab.svg'})

    def print_tail(self):
        self.end_node('Lexicon')
        self.end_node('LexicalResource')
        self.end_document()

    def print_lexeme(self, lexeme):
        item_id = f'{self.wordnet_id}-{self.dict_id}-{lexeme["entry"]}-{lexeme["id"]}'
        self.debug_id = item_id
        self.start_node('LexicalEntry', {'id':  item_id})

        # TODO uztaisīt no vārdšķiras
        if lexeme['paradigm'].startswith('noun'):
            lmfpos = 'n'
        elif lexeme['paradigm'].startswith('verb'):
            lmfpos = 'v'
        elif lexeme['paradigm'].startswith('adj') or lexeme['paradigm'].startswith('part-'):
            lmfpos = 'a'
        elif lexeme['paradigm'].startswith('adverb'):
            lmfpos = 'r'
        elif lexeme['paradigm'].startswith('prep'):
            lmfpos = 'p'
        elif 'paradigm' in lexeme:
            lmfpos = 'x'
        else:
            lmfpos = 'u'

        lemma_params = {'writtenForm': lexeme['lemma'], 'partOfSpeech': lmfpos}
        self.start_node('Lemma', lemma_params)

        self.end_node('Lemma')
        self.end_node('LexicalEntry')

    def print_synset(self, synset_id, synset_senses, synset_lexemes):
        item_id = f'{self.wordnet_id}-{self.dict_id}-{synset_id}'
        self.debug_id = item_id
        memberstr = ''
        for lexeme in synset_lexemes:
            memberstr = f'{memberstr} {self.wordnet_id}-{self.dict_id}-{lexeme.entry_hk}-{lexeme.lexeme_id}'
        self.start_node('Synset', {'id': item_id, 'ili': '0', 'members': memberstr.strip()})  # TODO
        for sense in synset_senses:
            if 'gloss' in sense:
                self.do_simple_leaf_node('Definition', {}, sense['gloss'])
        self.end_node('Synset')
