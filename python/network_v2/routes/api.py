from io import BytesIO
from flask import Blueprint, jsonify, request, send_file, session
import qrcode

from core import Wallet

from variables import blockchain

route = Blueprint("api", __name__, url_prefix="/api")


@route.route("/login", methods=["POST"])
def login():
    body = request.get_json()
    wallet = Wallet.from_dict(body)
    session["wallet"] = wallet.to_dict()
    return 200


@route.route("/signup", methods=["POST"])
def signup():
    wallet = Wallet()
    return jsonify(wallet.to_dict()), 201

def jsonify_transaction(transaction):
    return {
        "sender": transaction.sender,
        "recipient": transaction.recipient,
        "amount": transaction.amount,
        "time": transaction.timestamp,
    }

@route.route("/home", methods=["POST"])
def get_home():
    body = request.get_json()
    address = body["myAddress"]
    blocks = blockchain.chain
    transactions = sum([block.transactions for block in blocks], [])
    my_send_transactions = [
        transaction for transaction in transactions if transaction.sender == address
    ]
    my_receive_transactions = [
        transaction for transaction in transactions if transaction.recipient == address
    ]
    my_transactions = sorted(
        my_send_transactions + my_receive_transactions, key=lambda tx: tx.timestamp
    )
    my_transactions = my_transactions[:5]
    amount = sum([transaction.amount for transaction in my_receive_transactions]) - sum(
        [transaction.amount for transaction in my_send_transactions]
    )
    return (
        jsonify(
            {"transactions": [jsonify_transaction(tx) for tx in my_transactions], "balance": amount}
        ),
        200,
    )

@route.route("/wallet", methods=["POST"])
def post_wallet():
    body = request.get_json()
    address = body["myAddress"]
    blocks = blockchain.chain
    transactions = sum([block.transactions for block in blocks], [])
    my_send_transactions = [
        transaction for transaction in transactions if transaction.sender == address
    ]
    my_receive_transactions = [
        transaction for transaction in transactions if transaction.recipient == address
    ]
    my_transactions = sorted(
        my_send_transactions + my_receive_transactions, key=lambda tx: tx.timestamp
    )
    amount = sum([transaction.amount for transaction in my_receive_transactions]) - sum(
        [transaction.amount for transaction in my_send_transactions]
    )
    return (
        jsonify(
            {"transactions": [jsonify_transaction(tx) for tx in my_transactions], "balance": amount}
        ),
        200,
    )


@route.route("/send", methods=["POST"])
def post_send():
    body = request.get_json()
    wallet = Wallet.from_dict({
        "public_key": body["myAddress"],
        "private_key": body["privateKey"],
    })
    transaction = blockchain.new_transaction(
        wallet, body["sendAddress"], body["amount"]
    )
    return jsonify(jsonify_transaction(transaction)), 201


@route.route("/showQR", methods=["POST"])
@route.route("/printQR", methods=["POST"])
def get_qr():
    body = request.get_json()
    wallet = body["myAddress"]
    qr = qrcode.QRCode(version=None, box_size=10, border=2)
    qr.add_data(wallet)
    qr.make(fit=True)
    fill = request.args.get("fill") or "black"
    back_color = request.args.get("back_color") or "white"
    img = qr.make_image(fill_color=fill, back_color=back_color)
    return serve_pil_image(img)


def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, "JPEG", quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/jpeg")
