from lv.ailab.xmlutils.writer import XMLWriter


class LMFWriter(XMLWriter):
    debug_id = 0

    def __init__(self, file, dict_id):
        super().__init__(file, dict_id, "  ", "\n")

    def print_head(self, wordnet_vers):
        self.start_document('<!DOCTYPE LexicalResource SYSTEM "http://globalwordnet.github.io/schemas/WN-LMF-1.1.dtd">')
        self.start_node('LexicalResource', {'xmlns:dc': "http://purl.org/dc/elements/1.1/"})
        self.start_node('Lexicon', {'id': 'wordnet_lv',
                                    'label': 'Latvian Wordnet',
                                    'language': 'lv',
                                    'email': 'peteris@ailab.lv',
                                    'licence': 'https://creativecommons.org/licenses/by-nc/4.0/',
                                    'version': wordnet_vers,
                                    'url': 'https://wordnet.ailab.lv/',
                                    'citations': 'TODO',
                                    'logo': 'https://wordnet.ailab.lv/images/AILab.svg'})

    def print_tail(self):
        self.end_node('Lexicon')
        self.end_node('LexicalResource')
        self.end_document()

    def print_lexeme(self, lexeme):
        item_id = f'{self.dict_id}-{lexeme["entry"]}-{lexeme["id"]}'
        self.debug_id = item_id
        self.start_node('LexicalEntry', {'id':  item_id})

        # TODO uztaisīt no vārdšķiras
        lmfpos = 'u'
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
        elif 'paradigm'in lexeme:
            lmfpos = 'x'

        lemma_params = {'writtenForm': lexeme['lemma'], 'partOfSpeech': lmfpos}
        self.start_node('Lemma', lemma_params)

        self.end_node('Lemma')
        self.end_node('LexicalEntry')
