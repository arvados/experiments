import yaml
import command
import os
import pprint

from jsonschema.validators import Draft4Validator
from ref_resolver import from_url

def load(path):
    with open(path) as fp:
        return yaml.load(fp)

module_dir = os.path.dirname(os.path.abspath(__file__))

tool_schema = load(os.path.join(module_dir, 'tool.json'))
tool_schema["properties"]["inputs"]["$ref"] = "file:%s/metaschema.json" % module_dir
tool_schema["properties"]["outputs"]["$ref"] = "file:%s/metaschema.json" % module_dir
tool_schema = Draft4Validator(tool_schema)

class Tool(object):
    def __init__(self, toolpath_object):
        self.tool = toolpath_object
        tool_schema.validate(self.tool)

    def cli(self, joborder):
        Draft4Validator(self.tool['inputs']).validate(joborder['inputs'])
        return command.cs_expr(joborder, self.tool['command'])
