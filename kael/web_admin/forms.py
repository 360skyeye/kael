# -*- coding: utf-8 -*-
import os
import codecs
import yaml
from jinja2 import Template
from flask import current_app

_forms = {}


def get_mapping(blueprint, endpoint):
    global _forms
    if not _forms:
        forms_yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'forms.yml')
        with codecs.open(forms_yaml_path, 'rb', 'utf-8') as fp:
            t = Template(fp.read())
            yml = t.render({'settings': current_app.config})
            _forms = yaml.load(yml)
    return _forms.get(blueprint, {}).get(endpoint, {})
