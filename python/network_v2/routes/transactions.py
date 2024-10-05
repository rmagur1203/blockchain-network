import json
import requests
from flask import Blueprint, jsonify, request
from time import time

from core import SmartContract
from variables import blockchain

route = Blueprint(
    'transactions',
    __name__,
    url_prefix='/transactions'
)

@route.route('/', methods=['GET'])
def get_transactions():
    response = {
        'transactions': [transaction.to_dict() for transaction in blockchain.transactions],
    }
    return jsonify(response), 200

@route.route('/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    timestamp = values['timestamp'] if 'timestamp' in values else time()
    last_timestamp = blockchain.transactions[-1].timestamp if len(blockchain.transactions) > 0 else 0

    contract = SmartContract(values['contract']) if 'contract' in values else None

    if timestamp <= last_timestamp:
        return jsonify({'message': 'This transaction is already added'}), 200

    transaction = blockchain.new_transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount'],
        time=timestamp,
        contract=contract
    )

    for node in blockchain.nodes:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = transaction.to_dict()
        requests.post(node.path('/transactions/new'), headers=headers, data=json.dumps(data))
        print(f'Send transaction to >> {node}')

    response = {
        'message': f'Transaction will be added to Block',
        'contract': contract.to_dict() if contract else None
    }
    return jsonify(response), 201
