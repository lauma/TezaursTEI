from lv.ailab.tezdb.query_uttils import lmfiy_pos
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
                                    'license': 'https://creativecommons.org/licenses/by-nc/4.0/',
                                    'version': wordnet_vers,
                                    'url': 'https://wordnet.ailab.lv/',
                                    'citation': 'TODO',
                                    'logo': 'https://wordnet.ailab.lv/images/mazais-logo-ailab.svg'})

    def print_tail(self):
        self.end_node('Lexicon')
        self.end_node('LexicalResource')
        self.end_document()

    def print_lexeme(self, lexeme, synseted_senses):
        gen_id = f'{self.wordnet_id}-{self.dict_id}'
        item_id = f'{gen_id}-{lexeme["entry"]}-{lexeme["id"]}'
        self.debug_id = item_id
        self.start_node('LexicalEntry', {'id':  item_id})
        lmfpos = lmfiy_pos(lexeme['pos'], lexeme['abbr_type'], lexeme['lemma'])
        lemma_params = {'writtenForm': lexeme['lemma'], 'partOfSpeech': lmfpos}
        self.do_simple_leaf_node('Lemma', lemma_params)
        for syn_sense in synseted_senses:
            self.do_simple_leaf_node('Sense',
                    {'id': f'{gen_id}-{lexeme["entry"]}-{syn_sense["sense_id"]}',
                     'synset': f'{gen_id}-{syn_sense["synset_id"]}'})
        self.end_node('LexicalEntry')

    def print_synset(self, synset_id, synset_senses, synset_lexemes, relations, omw_relations):
        item_id = f'{self.wordnet_id}-{self.dict_id}-{synset_id}'
        self.debug_id = item_id
        memberstr = ''
        for lexeme in synset_lexemes:
            memberstr = f'{memberstr} {self.wordnet_id}-{self.dict_id}-{lexeme["entry"]}-{lexeme["lexeme_id"]}'
        ili = ''
        if omw_relations:
            if len(omw_relations) > 1:
                print(f'Synset {synset_id} has more than 1 OMW relation.')
            elif omw_relations[0]:
                ili = omw_relations[0]

        self.start_node('Synset', {'id': item_id, 'ili': ili, 'members': memberstr.strip()})
        unique_gloss = {}
        for sense in synset_senses:
            if 'gloss' in sense:
                unique_gloss[sense['gloss']] = 1
        for gloss in unique_gloss:
            self.do_simple_leaf_node('Definition', {}, gloss)
        for rel in relations:
            self.do_simple_leaf_node('SynsetRelation',
                                     {'relType': rel['other_name'],
                                      'target': f'{self.wordnet_id}-{self.dict_id}-{rel["other"]}'})
        self.end_node('Synset')
