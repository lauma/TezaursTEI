from lv.ailab.dictutils.gloss_normalization import full_cleanup
from lv.ailab.tezdb.query_uttils import lmfiy_pos, extract_paradigm_text
from lv.ailab.xmlutils.writer import XMLWriter


class LMFWriter(XMLWriter):
    #debug_id = 0

    def __init__(self, file, dict_version, wordnet_id):
        super().__init__(file, "  ", "\n")
        self.debug_id = 0
        self.wordnet_id = wordnet_id
        self.dict_version = dict_version

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
                                    'citation': 'Peteris Paikens, Agute Klints, Ilze Lokmane, Lauma Pretkalniņa, Laura '
                                                + 'Rituma, Madara Stāde and Laine Strankale. Latvian WordNet. '
                                                + 'Proceedings of Global Wordnet Conference, 2023.',
                                    'logo': 'https://wordnet.ailab.lv/images/mazais-logo-ailab.svg'})

    def print_tail(self):
        self.end_node('Lexicon')
        self.end_node('LexicalResource')
        self.end_document()

    def print_lexeme(self, lexeme, synseted_senses, print_tags):
        gen_id = f'{self.wordnet_id}-{self.dict_version}'
        item_id = f'{gen_id}-{lexeme["entry"]}-{lexeme["id"]}'
        self.debug_id = item_id
        self.start_node('LexicalEntry', {'id': item_id})
        lmfpos = lmfiy_pos(lexeme['pos'], lexeme['abbr_type'], lexeme['lemma'])
        lemma_params = {'writtenForm': lexeme['lemma'], 'partOfSpeech': lmfpos}
        self.do_simple_leaf_node('Lemma', lemma_params)
        if print_tags and 'paradigm' in lexeme:
            paradigm_text = extract_paradigm_text(lexeme['paradigm'])
            if paradigm_text:
                self.do_simple_leaf_node('Tag', {}, paradigm_text)
        for syn_sense in synseted_senses:
            self.do_simple_leaf_node('Sense', {'id': f'{gen_id}-{lexeme["entry"]}-{syn_sense["sense_id"]}',
                                               'synset': f'{gen_id}-{syn_sense["synset_id"]}'})
        self.end_node('LexicalEntry')

    def print_synset(self, synset_id, synset_senses, synset_lexemes, relations, pwn_relations, ili_map):
        item_id = f'{self.wordnet_id}-{self.dict_version}-{synset_id}'
        self.debug_id = item_id
        memberstr = ''
        for lexeme in synset_lexemes:
            memberstr = f'{memberstr} {self.wordnet_id}-{self.dict_version}-{lexeme["entry"]}-{lexeme["lexeme_id"]}'
        pnw_id = None
        if pwn_relations:
            if len(pwn_relations) > 1:
                print(f'Synset {synset_id} has more than 1 pwn-3.0 relation.')
            elif pwn_relations[0]['id']:
                pnw_id = pwn_relations[0]['id']
        ili = ili_map.get_mapping(pnw_id)

        self.start_node('Synset', {'id': item_id, 'ili': ili, 'members': memberstr.strip()})
        unique_gloss = {}
        for sense in synset_senses:
            if 'gloss' in sense:
                unique_gloss[full_cleanup(sense['gloss'])] = 1
        for gloss in unique_gloss:
            self.do_simple_leaf_node('Definition', {}, gloss)
        for rel in relations:
            self.do_simple_leaf_node('SynsetRelation',
                                     {'relType': rel['target_role'],
                                      'target': f'{self.wordnet_id}-{self.dict_version}-{rel["target_id"]}'})
        for sense in synset_senses:
            if 'examples' in sense:
                for example in sense['examples']:
                    attribs = {}
                    if 'source' in example:
                        attribs['source'] = example['source']
                    self.do_simple_leaf_node('Example', attribs, example['text'])
        self.end_node('Synset')
