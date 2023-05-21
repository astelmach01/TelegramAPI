from website import create_app
from website.settings import settings

app = create_app()


if __name__ == "__main__":
    debug = settings.ENVIRONMENT == "development"
    app.run(debug=False)
