import json
import os


META_PATH = os.path.join(os.path.dirname(__file__), "metadata")


def get_meta_from_json(metaname):
    metafile = os.path.join(META_PATH, f"{metaname}.json")
    with open(metafile) as json_data:
        meta = json.load(json_data)
    return meta
