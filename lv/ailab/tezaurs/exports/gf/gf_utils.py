from lv.ailab.tezaurs.utils.dict.db_wordform_utils import is_replacing_wordform_set, filter_wordforms
from lv.ailab.tezaurs.utils.dict.morpho_constants import MorphoVal, MorphoAttr


class GFUtils:

    INDENT = '  '
    BIG_SEPARATOR = '_'
    DEFAULT_LET_VARIABLE = 'l'
    GF_NUMBER_SINGULAR = 'Sg'
    GF_NUMBER_PLURAL = 'Pl'
    GF_CASE_VOCATIVE = 'Voc'

    DEFAULT_GF_POS = {
        MorphoVal.NOUN: "N",
        #TODO ... Other entries
    }

    @staticmethod
    def get_GF_pos(lexeme):
        result = GFUtils.DEFAULT_GF_POS[lexeme['pos']]
        if (lexeme['pos'] == MorphoVal.NOUN
                and MorphoAttr.NOUN_TYPE in lexeme['combined_flags']
                and lexeme['combined_flags'][MorphoAttr.NOUN_TYPE] == MorphoVal.PROPER_NOUN
                and MorphoAttr.PNOUN_TYPE in lexeme['combined_flags']
                and lexeme['combined_flags'][MorphoAttr.PNOUN_TYPE] == MorphoVal.PLACE_NAME):
            result = 'LN'
        return result


    @staticmethod
    def normalize_for_GF(paradigm):
        if not paradigm: return
        return paradigm.replace('-', GFUtils.BIG_SEPARATOR)


    @staticmethod
    def form_concrete_lex_expr(gf_tail, lemma, paradigm):
        gf_paradigm = GFUtils.normalize_for_GF(paradigm)
        return f'{gf_paradigm}_from{gf_tail} "{lemma}"'


    @staticmethod
    def form_synest_comment(synsets):
        if not synsets or len(synsets) < 1:
            return None
        result = GFUtils.INDENT * 3
        result = f"{result} -- {', '.join(sorted(synsets))}"
        return result


    # gf_std_form_string is something like `bro.s ! Sg ! Voc` - something to add to include standard forms from paradigm
    # Result is something like `variants{ "brāl" ; bro.s ! Sg ! Voc }`
    @staticmethod
    def _form_variant_list(wordforms, gf_std_form_string):
        if not wordforms or len(wordforms) < 1:
            return None
        include_standard_forms = not is_replacing_wordform_set(wordforms)
        result = " ; ".join(map(lambda wf: f"\"{wf['form']}\"", wordforms))
        if include_standard_forms:
            result = f"{result} ; {gf_std_form_string}"
        if len(wordforms) > 1 or include_standard_forms:
            result = f"variants {{ {result} }}"
        return result


    # Result is something like `{ Sg => old_noun.s ! Sg ** variants{ "brāl" ; bro.s ! Sg ! Voc } ; Pl => old_noun.s ! Pl ** { Voc = "brāļi" } }`
    @staticmethod
    def _form_table_with_vocative_extension(sg_voc_wordforms, pl_voc_wordforms):
        if ((not sg_voc_wordforms or len(sg_voc_wordforms) < 1)
                and (not pl_voc_wordforms or len(pl_voc_wordforms) < 1)):
            return None

        result = f"{GFUtils.GF_NUMBER_SINGULAR} => {GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_SINGULAR}"
        sg_voc = GFUtils._form_variant_list(
            sg_voc_wordforms, f"{GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_SINGULAR} ! {GFUtils.GF_CASE_VOCATIVE}")
        if sg_voc:
            result = f"{result} ** {{ {GFUtils.GF_CASE_VOCATIVE} => {sg_voc} }}"
        result = f"{result} ; "
        result = f"{result}{GFUtils.GF_NUMBER_PLURAL} => {GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_PLURAL}"
        pl_voc = GFUtils._form_variant_list(
            pl_voc_wordforms, f"{GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_PLURAL} ! {GFUtils.GF_CASE_VOCATIVE}")
        if sg_voc and pl_voc:
            result = f"{result} ** {{ {GFUtils.GF_CASE_VOCATIVE} => {pl_voc} }}"
        if pl_voc:
            result = f"{result}{GFUtils.GF_NUMBER_PLURAL} => {GFUtils.GF_CASE_VOCATIVE} => {pl_voc}"
        return f"table {{ {result} }}"


    # Here we form something like this:
    # let bro = noun_2a_fromLemma "brālis" in {
    #   s = table { Sg => bro.s ! Sg ** variants{ "brāl" ; bro.s ! Sg ! Voc } ;
    #     Pl => bro.s ! Pl ** { Voc => "brāļi" } } ;
    #   gend = bro.gend } ;
    @staticmethod
    def form_N_with_vocative_extension(lexeme, paradigm_expr):
        if 'wordforms' not in lexeme or not lexeme['wordforms'] or len(lexeme['wordforms']) < 1:
            return None
        sg_voc_wfs, leftover_wordforms = filter_wordforms(
            lexeme['wordforms'], {MorphoAttr.NUMBER: MorphoVal.SINGULAR, MorphoAttr.CASE: MorphoVal.VOCATIVE})
        pl_voc_wfs, leftover_wordforms = filter_wordforms(
            leftover_wordforms, {MorphoAttr.NUMBER: MorphoVal.PLURAL, MorphoAttr.CASE: MorphoVal.VOCATIVE})

        extended_gf_table = GFUtils._form_table_with_vocative_extension(sg_voc_wfs, pl_voc_wfs)

        if not extended_gf_table or leftover_wordforms and len(leftover_wordforms) > 0:
            print(f'Skipping {lexeme["lemma"]} because additional wordforms are not all vocatives!')
            return None

        return f"let {GFUtils.DEFAULT_LET_VARIABLE} = {paradigm_expr} in {{ s = {extended_gf_table} ; gend = {GFUtils.DEFAULT_LET_VARIABLE}.gend }}"


    @staticmethod
    # Result is something like `let l = noun_6b_fromNomPl "Cēsis" in { s = l.s ! Pl ; gend = l.gend ; num = Pl }`
    def _form_LN(paradigm_expr, number):
        return f"let {GFUtils.DEFAULT_LET_VARIABLE} = {paradigm_expr} in {{ s = {GFUtils.DEFAULT_LET_VARIABLE}.s ! {number} ; gend = {GFUtils.DEFAULT_LET_VARIABLE}.gend ; num = {number} }}"


    @staticmethod
    def form_LN_plural(paradim_expr):
        return GFUtils._form_LN(paradim_expr, GFUtils.GF_NUMBER_PLURAL)


    @staticmethod
    def form_LN_singular(paradim_expr):
        return GFUtils._form_LN(paradim_expr, GFUtils.GF_NUMBER_SINGULAR)