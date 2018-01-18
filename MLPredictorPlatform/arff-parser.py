import os
import io
import csv
from collections import namedtuple

COMMENT = '%'
SPECIAL = '@'
RELATION = '@relation'
ATTRIBUTE = '@attribute'
DATA = '@data'

def str_remove_quotes(obj):
    return str(obj[1:-1])

    
ARFF_TYPES = {
    'numeric': float,
    'integer': int,
    'real': float,
    'string': str_remove_quotes,
}

PYTHON_TYPES = {
    float: 'real',
    int: 'integer',
    str: 'string',
    bool: '{True, False}'
}

# python2/3 compatible unicode
def u(text):
    if str == bytes:
        return text.decode('utf-8')
    else:
        # python 3
        return text
    
    
class _Nominal:
    '''an enum in arff'''
    def __init__(self, name, type_text):
        self.name = name
        self.type_text = type_text
        values_str = type_text.strip('{} ')
        self.options = values_str.split()
        self.options = [opt.strip(', ') for opt in self.options]
    
    def parse(self, text):
        if text in self.options:
            return text
        else:
            raise ValueError("'%s' is not in {%s}" % (text, self.options))

class _SimpleType:
    def __init__(self, name, type_text):
        self.name = name
        self.type = ARFF_TYPES[type_text]
    def parse(self, text):
        return self.type(text)

def _field_type(name, type_text):
    if type_text in ARFF_TYPES:
        return _SimpleType(name, type_text)
    
    if type_text.startswith('{'):
        return _Nominal(name, type_text)
    
    raise ValueError("Unrecognized attribute type: %s" % type_text)

    #'date': date_format,


def _parse_types(row, fields):
    typed_row = []
    for i, ftype in enumerate(fields):
        typed_row.append(ftype.parse(row[i]))
    
    return typed_row

class _RowParser:
    def __init__(self, fields):
        self.fields = fields
        self.tuple = namedtuple('Row', [f.name for f in fields])
    
    def parse(self, row):
        values = []
        for f, item in zip(self.fields, row):
            values.append(f.parse(item))
        
        return self.tuple(*values)

def loads(text):
    if bytes == str:
        if type(text) != unicode:
            raise ValueError('arff.loads works with unicode strings only')
    else:
        if type(text) != str:
            raise ValueError('arff.loads works with strings only')
    lines_iterator = io.StringIO(text)
    for item in Reader(lines_iterator):
        yield item


def load(fname):
    with open(fname, 'r') as fhand:
        for item in Reader(fhand):
            yield item

class Reader:
    def __init__(self, lines_iterator):
        self.lines_iterator = lines_iterator
    def __iter__(self):
        lines_iterator = self.lines_iterator
        fields = []
        
        for line in lines_iterator:
            if line.startswith(COMMENT):
                continue
            
            if line.lower().startswith(DATA):
                break
            
            if line.lower().startswith(RELATION):
                _, relation = line.split()
                self.relation = relation
            
            if line.lower().startswith(ATTRIBUTE):
                space_separated = line.split(' ', 2)
                name = space_separated[1]
                field_type_text = space_separated[2].strip()
                
                fields.append(_field_type(name, field_type_text))
        
        self.fields = fields
        
        # data
        reader = csv.reader(lines_iterator)
        row_parser = _RowParser(fields)
        for row in reader:
            typed_row = row_parser.parse(row)
            yield typed_row


def _convert_row(row):
    items = [repr(item) for item in row]
    return ','.join(items)
        
def dumps(*args, **kwargs):
    items = []
    rows_gen = (row for row in dump_lines(*args, **kwargs))
    return u(os.linesep).join(rows_gen)

    
    

def dump_lines(row_iterator, relation='untitled', names=None):
    w = _LineWriter(relation, names)
    for row in row_iterator:
        for line in w.generate_lines(row):
            yield line
    

def dump(fname, row_iterator, relation='untitled', names=None):
    w = Writer(fname, relation, names)
    for row in row_iterator:
        w.write(row)
    w.close()

class _LineWriter:
    def __init__(self, relation='untitled', names=None):
        self.relation = relation
        self.names = names
        self._first_row = True
        self.pytypes = dict(PYTHON_TYPES)
        
    def generate_lines(self, row):
        if self._first_row:
            self._first_row = False
            ftypes = []
            for item in row:
                item_type = type(item)
                if item_type not in self.pytypes:
                    raise ValueError("Unknown type: %s" % item_type)
                ftypes.append(self.pytypes[item_type])
            if self.names is None:
                self.names = ['attr%d' % i for i in range(len(row))]
        
            yield "%s %s" % (RELATION, self.relation)
        
            for name, f in zip(self.names, ftypes):
                yield "%s %s %s" % (ATTRIBUTE, name, f)
        
            yield DATA
        
        yield _convert_row(row)
        


class Writer(_LineWriter):
    def __init__(self, fname, relation='untitled', names=None):
        self.fhand = open(fname, 'wb')
        _LineWriter.__init__(self, relation, names)
        
    def write(self, row):
        for line in self.generate_lines(row):
            line = line + os.linesep
            self.fhand.write(line.encode('utf-8'))
    
    def close(self):
        self.fhand.close()