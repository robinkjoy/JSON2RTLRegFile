import json
import jsonschema

schema = open("schema.json").read()
sample = open("sample.json").read()

try:
    v = jsonschema.Draft4Validator(json.loads(schema))
    for error in v.iter_errors(json.loads(sample)):
        print(error.message)
except jsonschema.ValidationError as e:
    print(e.message)
