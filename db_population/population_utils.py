import json
import os
from wam.settings import BASE_DIR

META_PATH = os.path.join(BASE_DIR, "stemp", "metadata")


def get_meta_from_json(metaname):
    metafile = os.path.join(META_PATH, f"{metaname}.json")
    with open(metafile) as json_data:
        meta = json.load(json_data)
    return meta
