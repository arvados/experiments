import os
import operator

from jsonschema import Draft4Validator
from cliche.ref_resolver import from_url


def evaluate(expression, job, context):
    vars = {
        'job': job,
        'self': context,
        'os': os
    }
    return eval(expression, vars)


class Argument(object):
    def __init__(self, job, value, schema, adapter=None):
        self.job = job
        self.schema = schema or {}
        if 'oneOf' in self.schema:
            self.schema = self._schema_from_opts(schema['oneOf'], value)
        self.adapter = adapter or self.schema.get('adapter', {})
        self.position = self.adapter.get('order', 99)
        self.prefix = self.adapter.get('prefix')
        self.separator = self.adapter.get('separator')
        if self.separator == ' ':
            self.separator = None
        self.item_separator = self.adapter.get('itemSeparator', ',')
        self.transform = self.adapter.get('transform')
        if self.transform:
            value = evaluate(self.transform, self.job, value)
        elif self.schema.get('type') in ('file', 'directory'):
            value = value['path']
        self.value = value

    def __int__(self):
        return bool(self.arg_list())

    def __unicode__(self):
        return unicode(self.value)

    def _schema_for(self, key):
        """ If value is object, get schema for its property. """
        if key in self.schema.get('properties', {}):
            return self.schema['properties'][key]

    def get_args_and_stdin(self, adapter_mixins=None):
        args = [Argument(self.job, v, self._schema_for(k)) for k, v in self.value.iteritems()]
        args += adapter_mixins or []
        args.sort(key=lambda x: x.position)
        stdin = [a.value for a in args if a.is_stdin()]
        return reduce(operator.add, [a.arg_list() for a in args], []), stdin[0] if stdin else None

    def arg_list(self):
        if self.is_stdin():
            return []
        if isinstance(self.value, dict):
            return self._as_dict()
        if isinstance(self.value, list):
            return self._as_list()
        return self._as_primitive()

    def is_stdin(self):
        return self.adapter.get('stdin')

    def _as_primitive(self):
        if self.value in (None, False):
            return []
        if self.value is True and (self.separator or not self.prefix):
            raise Exception('Boolean arguments must have a prefix and no separator.')
        if not self.prefix:
            return [self.value]
        if self.separator is None:
            return [self.prefix] if self.value is True else [self.prefix, self.value]
        return [self.prefix + self.separator + unicode(self.value)]

    def _as_dict(self):
        args = [Argument(self.job, v, self._schema_for(k)) for k, v in self.value.iteritems()]
        args.sort(key=lambda x: x.position)
        return reduce(operator.add, [a.arg_list() for a in args], [])

    def _as_list(self):
        item_schema = self.schema.get('items', {})
        args = [Argument(self.job, item, item_schema) for item in self.value]
        if not self.prefix:
            return reduce(operator.add, [a.arg_list() for a in args], [])
        if not self.separator and not self.item_separator:
            return reduce(operator.add, [[self.prefix] + a.arg_list() for a in args], [])
        if self.separator and not self.item_separator:
            return [self.prefix + self.separator + a._list_item() for a in args if a._list_item() is not None]
        args_as_strings = [a._list_item() for a in args if a._list_item() is not None]
        joined = self.item_separator.join(args_as_strings)
        if not self.separator and self.item_separator:
            return [self.prefix, joined]
        return [self.prefix + self.separator + joined]

    def _list_item(self):
        as_arg_list = self.arg_list()
        if not as_arg_list:
            return None
        if len(as_arg_list) > 1:
            raise Exception('Multiple arguments as part of str-separated list.')
        return unicode(as_arg_list[0])

    def _schema_from_opts(self, options, value):
        for opt in options:
            validator = Draft4Validator(opt)
            try:
                validator.validate(value)
                return opt
            except:
                pass
        raise Exception('No options valid for supplied value.')


class Adapter(object):
    def __init__(self, tool):
        self.tool = tool
        self.adapter = tool.get('adapter', {})
        self.base_cmd = self.adapter.get('baseCmd', [])
        if isinstance(self.base_cmd, basestring):
            self.base_cmd = self.base_cmd.split(' ')
        self.stdout = self.adapter.get('stdout')
        self.args = self.adapter.get('args', [])
        self.input_schema = self.tool.get('inputs')
        self.output_schema = self.tool.get('outputs')

    def _arg_list_and_stdin(self, job):
        adapter_args = [Argument(job, self._get_value(a, job), {}, a) for a in self.args]
        return Argument(job, job['inputs'], self.input_schema).get_args_and_stdin(adapter_args)

    def cmd_line(self, job):
        arg_list, stdin = self._arg_list_and_stdin(job)
        stdin = ['<', stdin] if stdin else []
        stdout = ['>', self.stdout] if self.stdout else []
        return ' '.join(map(unicode, self.base_cmd + arg_list + stdin + stdout))

    def _get_value(self, arg, job):
        value = arg.get('value')
        if not value:
            raise Exception('Value not specified for arg %s' % arg)
        if isinstance(value, dict) and '$expr' in value:
            value = evaluate(value['$expr'], job, None)
        return value


def cmd_line(doc_path, tool_key='tool', job_key='job'):
    doc = from_url(doc_path)
    tool, job = doc[tool_key], doc[job_key]
    return Adapter(tool).cmd_line(job)


def test_cmd_line(tool, job, test):
    result = Adapter(tool).cmd_line(job)
    if result == test['expected_cmd_line']:
        return True
    else:
        print 'Got:', result
        print 'Expected:', test['expected_cmd_line']
        return False


def run_tests(doc_path, tool_key='tool', test_key='tests'):
    doc = from_url(doc_path)
    tests = doc[test_key]
    for test in tests:
        tool = test.get(tool_key)
        if test_cmd_line(tool, test.get('test_job'), test):
            print 'Test %s completed successfully!' % test.get('id')
        else:
            print 'Test %s completed failed!' % test.get('id')


if __name__ == '__main__':
    print cmd_line(os.path.join(os.path.dirname(__file__), '../examples/tmap.yml'), 'mapall', 'exampleJob')
    print cmd_line(os.path.join(os.path.dirname(__file__), '../examples/bwa-mem.yml'))
    run_tests(os.path.join(os.path.dirname(__file__), '../examples/bwa-mem-test.yml'))



