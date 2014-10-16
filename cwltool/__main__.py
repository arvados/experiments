import tool
import argparse
from ref_resolver import from_url
import jsonschema

parser = argparse.ArgumentParser()
parser.add_argument("schema", type=str)
parser.add_argument("job_order", type=str)

args = parser.parse_args()

try:
    t = tool.Tool(from_url(args.schema))
except jsonschema.exceptions.ValidationError as e:
    print "Tool definition failed validation"
    print e

try:
    print t.cli(from_url(args.job_order))
except jsonschema.exceptions.ValidationError as e:
    print "Job order failed validation"
    print e
