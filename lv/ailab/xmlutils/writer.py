from xml.sax.saxutils import XMLGenerator

default_indent_chars = "  "
default_newline_chars = "\n"


class XMLWriter:

    def __init__(self, file, dict_id, indent_chars=default_indent_chars, newline_chars=default_newline_chars):
        self.indent_chars = indent_chars
        self.newline_chars = newline_chars
        self.file = file
        self.dict_id = dict_id
        self.gen = XMLGenerator(file, 'UTF-8', True)
        self.xml_depth = 0

    def start_node(self, name, attrs):
        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.startElement(name, attrs)
        self.gen.ignorableWhitespace(self.newline_chars)
        self.xml_depth = self.xml_depth + 1

    def end_node(self, name):
        self.xml_depth = self.xml_depth - 1
        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.endElement(name)
        self.gen.ignorableWhitespace(self.newline_chars)

    def do_simple_leaf_node(self, name, attrs, content):
        self.gen.ignorableWhitespace(self.indent_chars * self.xml_depth)
        self.gen.startElement(name, attrs)
        self.gen.characters(content)
        self.gen.endElement(name)
        self.gen.ignorableWhitespace(self.newline_chars)

    def start_document(self):
        self.gen.startDocument()

    def end_document(self):
        self.gen.endDocument()
