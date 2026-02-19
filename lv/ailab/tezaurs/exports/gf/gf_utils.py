class GFUtils:

    INDENT = '  '
    BIG_SEPARATOR = '_'

    @staticmethod
    def normalize_for_gf(paradigm):
        if not paradigm: return
        return paradigm.replace('-', GFUtils.BIG_SEPARATOR)