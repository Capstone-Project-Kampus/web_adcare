import os
import importlib
from flask import Blueprint

api_blueprints = []

# Loop semua file di folder api_v1
for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith("_controller.py") and file != "__init__.py":
        module_name = f"controllers.api.{file[:-3]}"
        module = importlib.import_module(module_name)

        # Cari semua atribut dalam module yang merupakan Blueprint dan memiliki nama diawali "admin"
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Blueprint) and attr_name.startswith("api"):
                api_blueprints.append(attr)
