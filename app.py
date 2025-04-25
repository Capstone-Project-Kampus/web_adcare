from flask import Flask, render_template
from controllers.api import api_blueprints
from controllers.cms import cms_blueprints

app = Flask(__name__)
# Register semua blueprint (API dan Admin) secara otomatis
for bp in api_blueprints + cms_blueprints:
    app.register_blueprint(bp)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")




if __name__ == "__main__":
    app.run(debug=True)
