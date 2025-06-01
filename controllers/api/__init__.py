import importlib
import os
from flask import current_app

# Dynamically import all modules in the current directory
current_dir = os.path.dirname(__file__)
module_names = [
    f[:-3] for f in os.listdir(current_dir) if f.endswith(".py") and f != "__init__.py" and f != "middleware.py"
]

api_blueprints = []


def init_api_routes(app, mongo):
    # Set mongo in app config for easy access in controllers
    app.config['MONGO'] = mongo
    
    # Import middleware for API key protection
    from .middleware import api_key_required
    
    # Make api_key_required available in app config
    app.config['API_KEY_REQUIRED'] = api_key_required
    
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

            # Special case for google_auth_controller
            if module_name == "google_auth_controller":
                from .google_auth_controller import init_google_auth_routes

                api_google_auth = init_google_auth_routes(app, mongo)
                api_blueprints.append(api_google_auth)

        except ImportError as e:
            print(f"Could not import {module_name}: {e}")

    return api_blueprints
