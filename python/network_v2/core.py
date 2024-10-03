if __package__ is None or __package__ == '':
    import sys
    from os import path
    sys.path.append(path.dirname(path.abspath(__file__)))

    from constants import DIFFICULTY
else:
    from .constants import DIFFICULTY

import math
from time import time
from typing import Any, List, Union
from urllib.parse import urlparse

import json
import hashlib
import random
import requests

class Transaction(object):
    def __init__(self, sender: str, recipient: str, amount: float, time: float):
        self.sender: str = sender
        self.recipient: str = recipient
        self.amount: float = amount
        self.timestamp: float = time
    
    @property
    def txid(self):
        return self.hash()
    
    @staticmethod
    def from_dict(data: dict):
        return Transaction(data['sender'], data['recipient'], data['amount'], data['timestamp'])
    
    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
        }

    def hash(self):
        return hashlib.sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()

class MerkleTree:
    def __init__(self, transactions: List[Transaction]):
        self.leaves = sorted([tx.hash() for tx in transactions])
        level = math.ceil(math.log2(len(self.leaves))) + 1
        self.tree = [0] + [0] * (2 ** level - 1)

        self.build_tree(1)
    
    @property
    def root(self):
        return self.tree[1]

    def build_tree(self, node: int) -> str:
        #TODO - 자식들 작은값이 왼쪽에 올 수 있도록 이진 탐색 트리로 구현

        # if start == end:
        #     self.tree[node] = self.leaves[start]
        #     return self.leaves[start]
        
        # mid = (start + end) // 2
        # left = self.build_tree(start, mid, 2 * node)
        # right = self.build_tree(mid + 1, end, 2 * node + 1)
        # self.tree[node] = self.hash_nodes(left, right)
        # return self.tree[node]
        depth = math.ceil(math.log2(len(self.leaves))) + 1
        if node >= 2 ** (depth - 1):
            index = node - 2 ** (depth - 1)
            self.tree[node] = self.leaves[index] if index < len(self.leaves) else 0
            if self.tree[node] == 0: # 만약 빈 노드면 형제 노드를 찾아서 복제
                self.tree[node] = self.leaves[index - 1]
            return self.tree[node]

        left = self.build_tree(2 * node)
        right = self.build_tree(2 * node + 1)
        self.tree[node] = self.hash_nodes(left, right)

        return self.tree[node]

    def hash_nodes(self, left, right):
        return hashlib.sha256((left + right).encode()).hexdigest()

    def get_root(self):
        return self.root

    def contains(self, tx: Transaction):
        leaf_hash = tx.hash()
        return leaf_hash in self.tree

    def get_proof(self, tx: Transaction):
        leaf_hash = tx.hash()
        if leaf_hash not in self.tree:
            return None  # 데이터가 트리에 없으면 증명할 수 없음

        index = self.tree.index(leaf_hash)
        proof = []

        # 리프 노드에서 루트 노드로 가는 경로의 형제 노드를 찾음
        while index > 1:
            if index % 2 == 0:  # 왼쪽 자식
                proof.append(self.tree[index + 1] if index + 1 < len(self.tree) else self.tree[index])
            else:  # 오른쪽 자식
                proof.append(self.tree[index - 1])
            index //= 2

        return proof

    def verify_proof(self, tx: Transaction, proof: List[str]):
        leaf_hash = tx.hash()
        computed_hash = leaf_hash

        for sibling_hash in proof:
            print(computed_hash, sibling_hash)
            if computed_hash < sibling_hash:
                computed_hash = self.hash_nodes(computed_hash, sibling_hash)
            else:
                computed_hash = self.hash_nodes(sibling_hash, computed_hash)
        
        print(computed_hash, self.root)

        return computed_hash == self.root

class BlockHeader(object):
    def __init__(self, timestamp: float, previous_hash: str, index: int, nonce: int):
        self.timestamp: float = timestamp
        self.previous_hash: str = previous_hash
        self.index: int = index
        self.nonce: int = nonce

    @staticmethod
    def from_dict(data: dict):
        return BlockHeader(data['timestamp'], data['previous_hash'], data['index'], data['nonce'])

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'index': self.index,
            'nonce': self.nonce,
        }
    
    def hash(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

class Block(object):
    def __init__(self, header: BlockHeader, transactions: List[Transaction]):
        self.header: BlockHeader = header
        self.transactions: List[Transaction] = transactions

    @staticmethod
    def from_dict(data: dict):
        return Block(BlockHeader.from_dict(data['header']), [Transaction.from_dict(tx) for tx in data['transactions']])

    def to_dict(self):
        return {
            'header': self.header.to_dict(),
            'transactions': [tx.to_dict() for tx in self.transactions],
        }
    
    def hash(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

class Node(object):
    def __init__(self, address: str):
        self.address: str = urlparse(address).netloc.replace("0.0.0.0", "localhost")

    def __str__(self):
        return f'http://{self.address}'

    def __eq__(self, other):
        # 다른 Node 객체와 비교
        return isinstance(other, Node) and self.address == other.address

    def __hash__(self):
        # 주소를 기반으로 해시값 생성
        return hash(self.address)
    
    def path(self, path: str) -> str:
        return f'http://{self.address}/{path}'

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.transactions: List[Transaction] = []
        self.nodes: set[Node] = set()

        # Create the genesis block
        self.new_block(index=1, previous_hash=1, nonce=100, time=0)

    @staticmethod
    def hash(block: Union[Block, Any]) -> str:
        if isinstance(block, Block):
            return block.hash()
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    @staticmethod
    def valid_pow(block: Block) -> bool:
        return block.hash()[:DIFFICULTY] == '0' * DIFFICULTY
    
    @property
    def last_block(self) -> Block:
        return self.chain[-1]
    
    def pow(self, block: Block) -> int:
        while self.valid_pow(block) is False:
            block.header.nonce = random.randint(0, 2**64)
            block.header.timestamp = time()
        return block.header.nonce
    
    def new_transaction(self, sender: str, recipient: str, amount: float, time=time()) -> Transaction:
        transaction = Transaction(sender, recipient, amount, time)
        self.transactions.append(transaction)
        return transaction
    
    def new_block(self, nonce: int, index=None, previous_hash=None, time=time()) -> Block:
        header = BlockHeader(time, previous_hash or self.hash(self.chain[-1]), index or self.chain[-1].header.index + 1, nonce)
        self.transactions.sort(key=lambda tx: tx.timestamp)
        block = Block(header, self.transactions)
        self.transactions = []
        self.chain.append(block)
        return block
    
    def valid_chain(self, chain: List[Block]) -> bool:
        prev_block = chain[0]
        for i in range(1, len(chain)):
            block = chain[i]
            if block.header.previous_hash != prev_block.hash():
                return False
            if not self.valid_pow(block):
                return False
            prev_block = block
        return True
    
    def register_node(self, address):
        if isinstance(address, str):
            address = Node(address)
        self.nodes.add(address)

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None # 가장 긴 체인
        longest = len(self.chain) # 가장 긴 체인 길이
        for node in neighbours: # 모든 이웃 노드에 대해 체인 길이를 비교
            response = requests.get(node.path('chain'))
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                chain = [Block.from_dict(block) for block in chain]
                if length > longest and self.valid_chain(chain): # 길이가 더 길고 유효한 체인이라면
                    longest = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False
