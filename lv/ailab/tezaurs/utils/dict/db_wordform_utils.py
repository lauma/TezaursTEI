# Returns tuple, first element is matching part of the set, second is non-matching
def filter_wordforms(source_set, filter_attributes):
    if not source_set or not filter_attributes:
        return source_set, []

    result_pos = []
    result_neg = []
    for wf in source_set:
        wf_fits_filter = True
        for attribute in filter_attributes.keys():
            if not 'flags' in wf:
                wf_fits_filter = False
            elif attribute in wf['flags'] and wf['flags'][attribute] != filter_attributes[attribute]\
                    and not filter_attributes[attribute] in wf['flags'][attribute]:
                wf_fits_filter = False
        if wf_fits_filter:
            result_pos.append(wf)
        else:
            result_neg.append(wf)

    return result_pos, result_neg


def is_replacing_wordform_set (wordforms):
    if not wordforms or len(wordforms) < 1:
        return False
    return any(filter(lambda wf : wf['replaces_base'], wordforms))
