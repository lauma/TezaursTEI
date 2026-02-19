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
        self.out.write(f'concrete {module_name} of {abs_module_name} = CatLav ** open ResLav, PortedMorphoParadigmsLav in {{\n')
        self.out.write('\n')
        self.out.write('flags\n')
        self.out.write(f'{GFUtils.INDENT}optimize=values ;\n')
        self.out.write(f'{GFUtils.INDENT}coding = utf8 ;\n')
        self.out.write('\n')

    def print_normal_lexeme(self, lemma, paradigm, postfix=None, synsets=None):
        self._print_lexeme('Lemma', lemma, paradigm, postfix, synsets)

    def print_plural_lexeme(self, lemma, paradigm, postfix=None, synsets=None):
        self._print_lexeme('NomPl', lemma, paradigm, postfix, synsets)

    def _print_lexeme(self, gf_tail, lemma, paradigm, postfix=None, synsets=None):
        if postfix is None:
            postfix = paradigm
        gf_paradigm = GFUtils.normalize_for_gf(paradigm)
        gf_postfix = GFUtils.normalize_for_gf(postfix)
        self.out.write(f'lin \'{lemma}_{gf_postfix}\' = {gf_paradigm}_from{gf_tail} "{lemma}"')
        #if len(synsets) > 0:
        #    self.out.write(f'{GFWriter.INDENT * 3}-- {", ".join(synsets)}')
        self.out.write(' ;\n')

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

    def print_lexeme(self, lemma, pos, postfix):
        gf_postfix = GFUtils.normalize_for_gf(postfix)

        self.out.write(f'fun \'{lemma}_{gf_postfix}\' : {pos} ; \n')


    def print_tail(self):
        self.out.write('}\n')
        self.out.close()