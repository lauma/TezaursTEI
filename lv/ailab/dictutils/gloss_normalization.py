import regex

superscript = {
    '1': "\u00B9",
    '2': "\u00B2",
    '3': "\u00B3",
    '0': "\u2070",
    '4': "\u2074",
    '5': "\u2075",
    '6': "\u2076",
    '7': "\u2077",
    '8': "\u2078",
    '9': "\u2079",
    '+': "\u207A",
    '-': "\u207B",
    '\u2013': "\u207B",
    '=': "\u207C",
    '(': "\u207D",
    ')': "\u207E",
    'i': "\u2071",
    'n': "\u207F",
    'x': "\u20E3",
}
subscript = {
    '0': "\u2080",
    '1': "\u2081",
    '2': "\u2082",
    '3': "\u2083",
    '4': "\u2084",
    '5': "\u2085",
    '6': "\u2086",
    '7': "\u2087",
    '8': "\u2088",
    '9': "\u2089",
    '+': "\u208A",
    '-': "\u208B",
    "\u2013": "\u208B",
    '=': "\u208C",
    '(': "\u208D",
    ')': "\u208E",
    'a': "\u2090",
    'e': "\u2091",
    'o': "\u2092",
    'x': "\u2093",
    'h': "\u2095",
    'k': "\u2096",
    'l': "\u2097",
    'm': "\u2098",
    'n': "\u2099",
    'p': "\u209A",
    's': "\u209B",
    't': "\u209C",
    "\u03B3": "\u1D67", # gamma
}


def _convert_to_sup(text, debug_text):
    warns = regex.findall('[^' + regex.escape(''.join(superscript.keys())) + ']', text)
    if warns:
        print(', '.join(warns) + " was not transformed to superscript in string \"" + text
              + "\" for full text \"" + debug_text + "\"!")
    result = text.translate(str.maketrans(superscript))
    return result


def _convert_to_sub(text, debug_text):
    warns = regex.findall('[^' + regex.escape(''.join(subscript.keys())) + ']', text)
    if warns:
        print(', '.join(warns) + " was not transformed to subscript in string \"" + text
              + "\" for full text \"" + debug_text + "\"!")
    result = text.translate(str.maketrans(subscript))
    return result


def normalize_scripts(gloss):
    result = gloss
    result = regex.sub(r'(?<!\\)\^([^ ]*?[^ \\])\^', lambda x: _convert_to_sup(x.group(1), gloss), result)
    result = regex.sub(r'(?<!\\)~([^ ]*?[^ \\])~', lambda x: _convert_to_sub(x.group(1), gloss), result)
    return result


def full_cleanup(gloss):
    result = gloss
    result = _remove_anchor_links(result)
    result = normalize_scripts(result)
    result = mandatory_normalization(result)
    result = _remove_emphasis(result)
    result = _unescape_tez_md(result)
    return result


def _remove_anchor_links(gloss):
    result = regex.sub(r'\[((?:\p{L}\p{M}*)+)]{[sen]:\d+}', r'\1', gloss)
    return result


def _remove_emphasis(gloss):
    result = gloss
    result = regex.sub('</?(em|i|small|b) ?/?>', '', result)
    result = regex.sub(r'(?<!\\)_+([^_]*[^_\\])_+', r'\1', result)
    return result


def mandatory_normalization(gloss):
    result = gloss
    result = _symbol_normalization(result)
    result = _normalize_spacing(result)
    return result


def _symbol_normalization(gloss):
    result = gloss
    result = regex.sub('--', '–', result)
    result = regex.sub('---', '—', result)
    result = regex.sub('\\.\\.\\.', '…', result)
    result = regex.sub('\\.\\.', '‥', result)
    result = regex.sub('-->', '→', result)
    return result


def _normalize_spacing(gloss):
    result = gloss
    result = regex.sub('\\n', ' ', result)
    result = regex.sub('  +', ' ', result)
    return result


def _unescape_tez_md(gloss):
    result = gloss
    result = regex.sub(r'\\_', '_', result)
    result = regex.sub(r'\\\^', '^', result)
    result = regex.sub(r'\\~', '~', result)
    return result

