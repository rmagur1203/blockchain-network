from flask import Blueprint, jsonify, request, session

from core import Wallet

route = Blueprint("api", __name__, url_prefix="/api")


@route.route("/login", methods=["POST"])
def get_wallet():
    body = request.get_json()
    wallet = Wallet.from_dict(body)
    session["wallet"] = wallet.to_dict()
    return 200


@route.route("/signup", methods=["POST"])
def post_wallet():
    wallet = Wallet()
    return jsonify(wallet.to_dict()), 201
