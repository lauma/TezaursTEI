from lv.ailab.tezaurs.utils.dict.db_wordform_utils import is_replacing_wordform_set


class GFUtils:

    INDENT = '  '
    BIG_SEPARATOR = '_'
    DEFAULT_LET_VARIABLE = 'l'
    GF_NUMBER_SINGULAR = 'Sg'
    GF_NUMBER_PLURAL = 'Pl'
    GF_CASE_VOCATIVE = 'Voc'


    @staticmethod
    def normalize_for_gf(paradigm):
        if not paradigm: return
        return paradigm.replace('-', GFUtils.BIG_SEPARATOR)


    @staticmethod
    def form_concrete_lex_expr(gf_tail, lemma, paradigm):
        gf_paradigm = GFUtils.normalize_for_gf(paradigm)
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
    def form_variant_list(wordforms, gf_std_form_string):
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
    def form_table_with_vocative_extension(sg_voc_wordforms, pl_voc_wordforms):
        if ((not sg_voc_wordforms or len(sg_voc_wordforms) < 1)
                and (not pl_voc_wordforms or len(pl_voc_wordforms) < 1)):
            return None

        result = f"{GFUtils.GF_NUMBER_SINGULAR} => {GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_SINGULAR}"
        sg_voc = GFUtils.form_variant_list(
            sg_voc_wordforms, f"{GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_SINGULAR} ! {GFUtils.GF_CASE_VOCATIVE}")
        if sg_voc:
            result = f"{result} ** {{ {GFUtils.GF_CASE_VOCATIVE} => {sg_voc} }}"
        result = f"{result} ; "
        result = f"{result}{GFUtils.GF_NUMBER_PLURAL} => {GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_PLURAL}"
        pl_voc = GFUtils.form_variant_list(
            pl_voc_wordforms, f"{GFUtils.DEFAULT_LET_VARIABLE}.s ! {GFUtils.GF_NUMBER_PLURAL} ! {GFUtils.GF_CASE_VOCATIVE}")
        if sg_voc and pl_voc:
            result = f"{result} ** {{ {GFUtils.GF_CASE_VOCATIVE} => {pl_voc} }}"
        if pl_voc:
            result = f"{result}{GFUtils.GF_NUMBER_PLURAL} => {GFUtils.GF_CASE_VOCATIVE} => {pl_voc}"
        return f"table {{ {result} }}"
