"""openapi.yaml must list every route this Flask app serves, with the same methods."""
import os
import re

import yaml

SPEC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi.yaml")


def test_every_route_is_documented(app):
    spec = yaml.safe_load(open(SPEC))
    documented = {
        (path, method.upper())
        for path, item in spec["paths"].items()
        for method in item
        if method in ("get", "post", "put", "delete", "patch")
    }
    served = {
        (re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule), method)
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    assert served <= documented, f"missing from openapi.yaml: {sorted(served - documented)}"
