import re


def prettify_pronunciation(pronunciation):
    pronunciation = pronunciation.strip()
    pronunciation = re.sub(',', "\u0327", pronunciation)
    pronunciation = re.sub('~', "\u0303", pronunciation)
    pronunciation = re.sub('^', "\u0302", pronunciation)
    pronunciation = re.sub(r"\\", "\u0300", pronunciation)
    pronunciation = re.sub('!', "\u02c8", pronunciation)
    pronunciation = re.sub('%', "\u02b2", pronunciation)
    return pronunciation


def prettify_text_with_pronunciation(text):
    return re.sub(r"\[[^\[\]]+]", lambda x: prettify_pronunciation(x.group(0)), text)
