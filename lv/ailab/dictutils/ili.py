import regex


class IliMapping:
    mapping_file = ''
    mapping = {}

    def __init__(self, path='config/ili-map-pwn30.tab'):
        self.mapping_file = path
        with open(self.mapping_file, 'r', encoding='utf8') as f:
            print(f'Loading ili mapping from {self.mapping_file}')
            for line in f:
                parts = regex.split('\t', line)
                if len(parts) == 2:
                    self.mapping[parts[1].strip()] = parts[0].strip()
                elif line:
                    print(f'Could not parse line: {line}')
            print('Done')

    def get_mapping(self, pnw_id):
        if not pnw_id:
            return ''
        if pnw_id not in self.mapping or not self.mapping[pnw_id]:
            print(f'No ili mapping for {pnw_id}')
            return ''
        return self.mapping[pnw_id]
