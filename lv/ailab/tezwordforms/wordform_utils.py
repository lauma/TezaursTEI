import json

from dictdiffer.testing import assert_no_diff


class LexemeProperties:

    ispell_omit_lexeme_flags = {
        "Valodas normēšana": ["Nevēlams"],
        "Lietojums": ["Apvidvārds", "Barbarisms", "Bērnu valoda", "Dialektisms", "Īsziņās", "Lamuvārds", "Neaktuāls", "Neliterārs", "Nevēlams", "Novecojis", "Okazionālisms", "Sarunā ar bērniem", "Sarunvaloda", "Sens, reti lietots vārds", "Slengs", "Vulgārisms", "Žargonisms"],
        "Stils" : ["Vienkāršrunas stilistiskā nokrāsa"],
        "Dialekta iezīmes": [], # Empty list means any value disqualifies
        "Izlokšņu grupa": [],
        "Izloksne": [],
        "Vārdšķira" : ["Reziduālis", "Vārds svešvalodā"]
    }
    ispell_omit_form_flags = {
        "Pakāpe": ["Pārākā", "Vispārākā"]
    }
    ispell_omit_paradigms = ["foreign", "number", "punct", "residual"]

    def __init__(self, lexeme_properties_path):
        with open(lexeme_properties_path, 'r', encoding='utf8') as file:
            self.lexeme_properties = json.load(file)

    @staticmethod
    def _flags_match_omit(flags, criteria):
        if not flags or len(flags) < 1:
            return False
        for flag_type in criteria:
            if flag_type in flags and len(flags[flag_type])> 0:
                if len(criteria[flag_type]) < 1:
                    return True
                else:
                    for flag_value in criteria[flag_type]:
                        if flag_value in flags[flag_type] or flags[flag_type] == flag_value:
                            return True
        return False

    # Checks if at least one of the lexemes associated with the given inflection path
    # matches the criteria for being included in spellchecker output (not regional, rude, etc.)
    def lexeme_good_for_spelling(self, inflection_path):
        if not inflection_path in self.lexeme_properties:
            return False
        properties_list = self.lexeme_properties[inflection_path]
        if len(properties_list) < 1:
            return False
        for property_set in properties_list:
            is_good = True
            if property_set["paradigm"] in self.ispell_omit_paradigms:
                # is_good = False
                continue
            if "flags" in property_set:
                is_good = not self._flags_match_omit(property_set["flags"], self.ispell_omit_lexeme_flags)
            if is_good:
                return True
        return False

    def form_good_for_spelling(self, form_property_map):
        bad = self._flags_match_omit(form_property_map, self.ispell_omit_form_flags) \
               or self._flags_match_omit(form_property_map, self.ispell_omit_lexeme_flags)
        return not bad


class WordformReader:

    def __init__(self, wordform_list_path):
        self.wordform_file = open(wordform_list_path, 'r', encoding='utf8')

    def process_line_by_line(self):
        for line in self.wordform_file:
            try:
                json_result = json.loads("{" + line.rstrip(", \n\r") + "}")
            except ValueError as e:
                continue
            yield json_result