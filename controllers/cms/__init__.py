
import os
import importlib
from flask import Blueprint

cms_blueprints = []

# Loop semua file di folder cms
for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith("_controller.py") and file != "__init__.py":
        module_name = f"controllers.cms.{file[:-3]}"
        module = importlib.import_module(module_name)

        # Cari semua atribut dalam module yang merupakan Blueprint dan memiliki nama diawali "admin"
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Blueprint) and attr_name.startswith("admin"):
                cms_blueprints.append(attr)
