from lv.ailab.xmlutils.writer import XMLWriter


class LMFWriter(XMLWriter):
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
