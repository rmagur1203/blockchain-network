import json
import requests
from flask import Blueprint, jsonify, request
from time import time

from core import Wallet
from variables import blockchain

route = Blueprint("transactions", __name__, url_prefix="/transactions")


@route.route("/", methods=["GET"])
def get_transactions():
    response = {
        "transactions": [
            transaction.to_dict() for transaction in blockchain.transactions
        ],
    }
    return jsonify(response), 200


@route.route("/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    required = ["sender", "private_key", "recipient", "amount"]
    if not all(k in values for k in required):
        return "Missing values", 400

    timestamp = values["timestamp"] if "timestamp" in values else time()
    last_timestamp = (
        blockchain.transactions[-1].timestamp if len(blockchain.transactions) > 0 else 0
    )

    if timestamp <= last_timestamp:
        return jsonify({"message": "This transaction is already added"}), 200

    transaction = blockchain.new_transaction(
        Wallet.from_dict(
            {"public_key": values["sender"], "private_key": values["private_key"]}
        ),
        values["recipient"],
        values["amount"],
        timestamp,
    )

    for node in blockchain.nodes:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = transaction.to_dict()
        requests.post(
            node.path("/transactions/new"), headers=headers, data=json.dumps(data)
        )
        print(f"Send transaction to >> {node}")

    response = {"message": f"Transaction will be added to Block"}
    return jsonify(response), 201
