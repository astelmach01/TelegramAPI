from quart import Blueprint

auth = Blueprint("auth", __name__)


@auth.route("/", methods=["POST"])
async def start():
    pass