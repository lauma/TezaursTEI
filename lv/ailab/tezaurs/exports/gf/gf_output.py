from lv.ailab.tezaurs.exports.gf.gf_utils import GFUtils


class GFConcreteWriter:

    def __init__(self, output_file):
        self.out = open(output_file, 'w', encoding='utf8')

    def print_head(self, module_name, abs_module_name, version):
        self.out.write('--# -path=.:abstract:common:prelude\n')
        self.out.write('\n')
        self.out.write(f'-- Contents of this file are automatically exported Tēzaurs lexicon, version {version}.\n')
        self.out.write('-- NB: Do NOT edit this without consulting lauma@ailab.lv or normundsg@ailab.lv\n')
        self.out.write('--     Otherwise your changes might get accidentally revoked!\n')
        self.out.write('\n')
        self.out.write('-- TODO and missing (compared to full Tēzaurs)\n')
        self.out.write('-- Nouns:\n')
        self.out.write('--   - Nouns with nonstandard forms any other than vocatives (vecāmāte, dievs)\n')
        self.out.write('--   - Nouns with other gender than paradigm\'s default (ļaudis) \n')
        self.out.write('-- Anything not noun:\n')
        self.out.write('--   - Everything :) \n')
        self.out.write('\n')
        self.out.write(f'concrete {module_name} of {abs_module_name} = CatLav ** open ResLav, PortedMorphoParadigmsLav in {{\n')
        self.out.write('\n')
        self.out.write('flags\n')
        self.out.write(f'{GFUtils.INDENT}optimize = values ;\n')
        self.out.write(f'{GFUtils.INDENT}coding = utf8 ;\n')
        self.out.write('\n')


    def print_lexeme(self, lemma, postfix, expression, synset_string=None):
        self.out.write(f'lin \'{lemma}_{postfix}\' = {expression} ;')
        if synset_string:
            self.out.write(synset_string)
        self.out.write('\n')


    def print_tail(self):
        self.out.write('}\n')
        self.out.close()

class GFAbstractWriter:

    def __init__(self, output_file):
        self.out = open(output_file, 'w', encoding='utf8')

    def print_head(self, module_name, version):
        self.out.write(f'-- Contents of this file are automatically exported Tēzaurs lexicon, version {version}.\n')
        self.out.write('-- NB: Do NOT edit this without consulting lauma@ailab.lv or normundsg@ailab.lv\n')
        self.out.write('--     Otherwise your changes might get accidentally revoked!\n')
        self.out.write('\n')
        self.out.write(f'abstract {module_name} = Cat ** {{\n')
        self.out.write('\n')
        self.out.write('flags coding = utf8 ;\n')
        self.out.write('\n')

    def print_lexeme(self, lemma, postfix, pos, synset_string=None):
        gf_postfix = GFUtils.normalize_for_GF(postfix)

        self.out.write(f'fun \'{lemma}_{gf_postfix}\' : {pos} ;')
        if synset_string:
            self.out.write(synset_string)
        self.out.write('\n')


    def print_tail(self):
        self.out.write('}\n')
        self.out.close()