from website import create_app, settings

app = create_app()


if __name__ == "__main__":
    debug = settings.ENVIRONMENT == "development"
    app.run(debug=debug)
