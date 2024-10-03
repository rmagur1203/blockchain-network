import json
import requests
from flask import Blueprint, jsonify, request

from variables import blockchain, port
from core import Node


route = Blueprint(
    'nodes',
    __name__,
    url_prefix='/nodes'
)

@route.route('/', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200

@route.route('/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    
    required = ['nodes']
    if not all(k in values for k in required):
        return 'Missing values', 400

    node = Node(values['nodes'])
    if node in blockchain.nodes:
        response = {
            'message': 'Node already registered',
            'total_nodes': [str(node) for node in blockchain.nodes],
        }
        return jsonify(response), 200
    
    print("Register node >> ", node)
    blockchain.register_node(node)
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {
        "nodes": 'http://localhost:' + str(port)
    }
    requests.post(node.path('/nodes/register'), headers=headers, data=json.dumps(data))

    for add_node in blockchain.nodes:
        if add_node != node:
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            data = {
                "nodes": str(node)
            }
            requests.post(add_node.path('/nodes/register'), headers=headers, data=json.dumps(data))
    
    response = {
        'message': 'New nodes have been added',
        'total_nodes': [str(node) for node in blockchain.nodes],
    }
    return jsonify(response), 201

