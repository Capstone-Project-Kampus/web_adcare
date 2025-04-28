from app import create_app

app, mongo, jwt = create_app()

if __name__ == "__main__":
    app.run(debug=True)
