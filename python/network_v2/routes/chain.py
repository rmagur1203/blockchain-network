from flask import Blueprint, jsonify, request
from time import time

import json
import requests

from variables import blockchain, mine_owner, mine_profit, node_id, port
from core import Block, BlockHeader, Transaction

route = Blueprint(
    'chain',
    __name__,
    url_prefix='/chain'
)

@route.route('/', methods=['GET'])
def get_chain():
    response = {
        'chain': [block.to_dict() for block in blockchain.chain],
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@route.route('/mine', methods=['GET'])
def mine():
    print("### MINING STARTED ###")
    
    coinbase = blockchain.new_transaction(
        sender=mine_owner,
        recipient=node_id,
        amount=mine_profit
    )
    block = blockchain.new_block(0)

    proof = blockchain.pow(block)

    print(f"### MINING FINISHED {proof} ###")

    for node in blockchain.nodes:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = {
            'miner': f'http://localhost:{port}',
            'header': block.header.to_dict(),
            'transactions': [transaction.to_dict() for transaction in block.transactions]
        }
        alarm_res = requests.post(node.path('/chain/resolve'), headers=headers, data=json.dumps(data))
        print(f'Send block to >> {node}')
        if alarm_res.status_code != 200:
            print(f'Error from >> {node}')
            blockchain.pow(block)


    response = {
        'message': "New Block Forged",
        'index': block.header.index,
        'transactions': [transaction.to_dict() for transaction in block.transactions],
        'proof': block.header.nonce,
        'previous_hash': block.header.previous_hash,
    }
    return jsonify(response), 200

@route.route('/resolve', methods=['POST'])
def resolve_chain():
    values = request.get_json()

    header = BlockHeader.from_dict(values['header'])
    transactions = [Transaction.from_dict(transaction) for transaction in values['transactions']]
    block = Block(header, transactions)

    if blockchain.valid_chain([*blockchain.chain, block]):
        blockchain.chain.append(block)
        blockchain.transactions = []
        print("New block added to chain")
        return jsonify({'message': 'New block added to chain'}), 200

    print("New block rejected")
    return jsonify({'message': 'New block rejected'}), 409