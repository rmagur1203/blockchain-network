if __package__ is None or __package__ == '':
    import sys
    from os import path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

    from one_node.base import Blockchain
    from util import is_port_in_use
else:
    from ..one_node.base import Blockchain
    from ..util import is_port_in_use
from flask import Flask, request, jsonify
from time import time

import requests
import json
import hashlib

blockchain = Blockchain()
my_ip = '0.0.0.0'
my_port = '5000'
node_identifier = f'node_{my_port}'
mine_owner = 'master'
mine_profit = 0.1

# 포트가 사용중이면 다음 포트로 변경
while is_port_in_use(int(my_port)):
    my_port = str(int(my_port) + 1)

app = Flask(__name__)

@app.route('/chain', methods=['GET'])
def full_chain():
    print("chain info requested!")
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/transactions', methods=['GET'])
def get_transactions():
    response = {
        'transactions': blockchain.current_transactions,
    }
    return jsonify(response), 200

@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()  # json 형태로 보내면 노드가 저장됨
    print("register nodes !!! : ", values)
    
    registering_node = values.get('nodes').replace("0.0.0.0", "localhost")
    if registering_node is None:  # 요청된 node 값이 없다면!
        return "Error: Please supply a valid list of nodes", 400
    
    # 요청받은 노드가 이미 등록된 노드와 중복인지 검사
    if registering_node.split("//")[1] in blockchain.nodes:
        print("Node already registered")  # 이미 등록된 노드입니다.
        response = {
            'message': 'Already Registered Node',
            'total_nodes': list(blockchain.nodes),
        }
    else:
        # 내 노드 리스트에 추가
        blockchain.register_node(registering_node)
        # 이후 해당 노드에 내 정보 등록하기
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = {
            "nodes": 'http://' + my_ip + ':' + str(my_port)
        }
        print("MY NODE INFO ", 'http://' + my_ip + ':' + str(my_port))
        requests.post(registering_node + "/nodes/register", headers=headers, data=json.dumps(data))
        
        # 이후 주변 노드들에도 새로운 노드가 등장함을 전파
        for add_node in blockchain.nodes:
            if add_node != registering_node.split("//")[1]:
                print('add_node : ', add_node)
                # 노드 등록하기
                headers = {'Content-Type': 'application/json; charset=utf-8'}
                data = {
                    "nodes": registering_node
                }
                requests.post('http://' + add_node + "/nodes/register", headers=headers, data=json.dumps(data))
        
        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(blockchain.nodes),
        }
    return jsonify(response), 201

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    print("transactions_new!!! : ", values)
    
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'missing values', 400
    
    timestamp = values['timestamp'] if 'timestamp' in values else time()
    last_timestamp = blockchain.current_transactions[-1]['timestamp'] if len(blockchain.current_transactions) > 0 else 0

    if timestamp == last_timestamp:
        return jsonify({'message': 'This transaction is already added'}), 200

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], timestamp)
    response = {'message': f'Transaction will be added to Block {index}'}
    
    # 노드 연결을 위해 추가되는 부분
    # 본 노드에 받은 거래 내역 정보를 다른 노드들에 다같이 업데이트해 준다.
    for node in blockchain.nodes:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = {
            "sender": values['sender'],
            "recipient": values['recipient'],
            "amount": values['amount'],
            "timestamp": timestamp,
            "type": "sharing"  # 전파이기에 sharing이라는 type이 꼭 필요
        }
        requests.post(f"http://{node}/transactions/new", headers=headers, data=json.dumps(data))
        print(f"share transaction to >> http://{node}")
    
    return jsonify(response), 201

@app.route('/mine', methods=['GET'])
def mine():
    print("MINING STARTED")
    last_block = blockchain.last_block
    last_proof = last_block['nonce']
    proof = blockchain.pow(last_proof)
    blockchain.new_transaction(
        sender=mine_owner,
        recipient=node_identifier,
        amount=mine_profit  # coinbase transaction
    )
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    print("MINING FINISHED")
    ################### 노드 연결을 위해 추가되는 부분
    response = None
    for node in blockchain.nodes:  # nodes에 연결된 모든 노드에 작업 증명(PoW)이 완료되었음을 전파한다.
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = {
            'miner_node': 'http://' + my_ip + ':' + str(my_port),
            'new_nonce': blockchain.last_block['nonce']
        }
        alarm_res = requests.get("http://" + node + "/nodes/resolve", headers=headers, data=json.dumps(data))
        if "ERROR" not in alarm_res.text:  # 전파 받은 노드의 응답에 ERROR라는 이야기가 없으면(나의 PoW가 인정받으면)
            ## 정상 response
            response = {
                'message': 'new block completed',
                'index': block['index'],
                'transactions': block['transactions'],
                'nonce': block['nonce'],
                'previous_hash': block['previous_hash'],
            }
        else: # 전파받은 노드의 응답에 이상이 있음을 알린다면?
            ## 내 PoW가 이상이 있을 수 있기에 다시 PoW 진행!
            block = blockchain.new_block(proof, previous_hash)
    
    return jsonify(response), 200

## 타 노드에서 블록 생성 내용을 전파하였을 때 검증 작업을 진행한다.
@app.route('/nodes/resolve', methods=['GET'])
def resolve():
    requester_node_info = request.get_json()
    required = ['miner_node']  # 해당 데이터가 존재해야 함
    # 데이터가 없으면 에러를 띄움
    if not all(k in requester_node_info for k in required):
        return 'missing values', 400
    ## 그전에 우선 previous에서 바뀐 것이 있는지 점검하자!!
    my_previous_hash = blockchain.last_block['previous_hash']
    last_proof = blockchain.last_block['nonce']
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    miner_chain_info = requests.get(requester_node_info['miner_node'].replace("0.0.0.0", "localhost") + "/chain", headers=headers)
    print("다른노드에서 요청이 온 블록, 검증 시작")
    print("miner_chain_info : ", miner_chain_info.text)
    new_block_previous_hash = json.loads(miner_chain_info.text)['chain'][-2]['previous_hash']
    print("new_block_previous_hash : ", new_block_previous_hash)
    print("my_previous_hash : ", my_previous_hash)
    # 내 노드의 전 해시와 새로 만든 노드의 전 해시가 같을 때!!! >> 정상
    if my_previous_hash == new_block_previous_hash and \
            blockchain.valid_proof(last_proof, int(requester_node_info['new_nonce'])):
        # 정말 PoW의 조건을 만족시켰을까? 검증하기
        print("다른노드에서 요청이 온 블록, 검증결과 정상!!!!!!")
        replaced = blockchain.resolve_conflicts()  # 결과값 : True Flase / True 면 내 블록의 길이가 짧아 대체되어야 한다.
        # 체인 변경 알림 메시지
        if replaced:
            ## 내 체이이 깗아서 대체되어야 함
            print("REPLACED length :", len(blockchain.chain))
            response = {
                'message': 'Our chain was replaced >> ' + my_ip + ":" + my_port,
                'new_chain': blockchain.chain
            }
        else:
            response = {
                'message': 'Our chain is authoritative',
                'chain': blockchain.chain
            }
    # 아니면 무엇인가 과거 데이터가 바뀐 것이다!!
    else:
        print("다른노드에서 요청이 온 블록, 검증결과 이상발생!!!!!!!!")
        response = {
            'message': 'Our chain is authoritative >> ' + my_ip + ":" + my_port,
            'chain': blockchain.chain
        }
    return jsonify(response), 200

def register_node():
    if my_port == 5000:
        return
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {
        "nodes": 'http://localhost:' + str(my_port)
    }
    requests.post("http://localhost:5000/nodes/register", headers=headers, data=json.dumps(data))
    print("register node to http://localhost:5000")

if __name__ == '__main__':
    app.run(host=my_ip, port=my_port)