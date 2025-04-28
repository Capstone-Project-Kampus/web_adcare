import importlib
import os

# Dynamically import all modules in the current directory
current_dir = os.path.dirname(__file__)
module_names = [
    f[:-3] for f in os.listdir(current_dir) if f.endswith(".py") and f != "__init__.py"
]

api_blueprints = []


def init_api_routes(app, mongo):
    for module_name in module_names:
        try:
            module = importlib.import_module(
                f".{module_name}", package="controllers.api"
            )

            # Check if the module has an init_routes function
            if hasattr(module, f"init_{module_name}_routes"):
                route_func = getattr(module, f"init_{module_name}_routes")
                blueprint = route_func(app, mongo)
                api_blueprints.append(blueprint)

            # Special case for auth_controller
            if module_name == "auth_controller":
                from .auth_controller import init_auth_routes

                api_auth = init_auth_routes(app, mongo)
                api_blueprints.append(api_auth)

        except ImportError as e:
            print(f"Could not import {module_name}: {e}")

    return api_blueprints
