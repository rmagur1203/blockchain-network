if __package__ is None or __package__ == "":
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
import rsa


class Wallet(object):
    def __init__(self):
        self.public_key, self.private_key = rsa.newkeys(512)

    def sign(self, message: str) -> str:
        return rsa.sign(message.encode(), self.private_key, "SHA-1").hex()

    def verify(self, message: str, signature: str) -> bool:
        return rsa.verify(message.encode(), bytes.fromhex(signature), self.public_key)

    @property
    def address(self) -> str:
        return self.public_key.save_pkcs1().hex()  # 공개키

    def to_dict(self):
        return {
            "address": self.address,
            "public_key": self.public_key.save_pkcs1().hex(),
            "private_key": self.private_key.save_pkcs1().hex(),
        }

    @staticmethod
    def from_dict(data: dict):
        wallet = Wallet()
        wallet.public_key = rsa.PublicKey.load_pkcs1(bytes.fromhex(data["public_key"]))
        wallet.private_key = rsa.PrivateKey.load_pkcs1(
            bytes.fromhex(data["private_key"])
        )
        return wallet


class Transaction(object):
    def __init__(
        self,
        sender: str | Wallet,
        recipient: str,
        amount: float,
        time: float,
        signature="",
    ):
        self.sender: str = sender.address if isinstance(sender, Wallet) else sender
        self.recipient: str = recipient
        self.amount: float = amount
        self.timestamp: float = time
        self.signature: str = (
            sender.sign(self.hash()) if isinstance(sender, Wallet) else signature
        )

    @property
    def txid(self):
        return self.hash()

    @staticmethod
    def from_dict(data: dict):
        return Transaction(
            data["sender"],
            data["recipient"],
            data["amount"],
            data["timestamp"],
            data["signature"],
        )

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    def hash(self):
        values = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
        }
        return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


class BlockHeader(object):
    def __init__(self, timestamp: float, previous_hash: str, index: int, nonce: int):
        self.timestamp: float = timestamp
        self.previous_hash: str = previous_hash
        self.index: int = index
        self.nonce: int = nonce

    @staticmethod
    def from_dict(data: dict):
        return BlockHeader(
            data["timestamp"], data["previous_hash"], data["index"], data["nonce"]
        )

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "index": self.index,
            "nonce": self.nonce,
        }

    def hash(self):
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()
        ).hexdigest()


class Block(object):
    def __init__(self, header: BlockHeader, transactions: List[Transaction]):
        self.header: BlockHeader = header
        self.transactions: List[Transaction] = transactions

    @staticmethod
    def from_dict(data: dict):
        return Block(
            BlockHeader.from_dict(data["header"]),
            [Transaction.from_dict(tx) for tx in data["transactions"]],
        )

    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    def hash(self):
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()
        ).hexdigest()


class Node(object):
    def __init__(self, address: str):
        self.address: str = urlparse(address).netloc.replace("0.0.0.0", "localhost")

    def __str__(self):
        return f"http://{self.address}"

    def __eq__(self, other):
        # 다른 Node 객체와 비교
        return isinstance(other, Node) and self.address == other.address

    def __hash__(self):
        # 주소를 기반으로 해시값 생성
        return hash(self.address)

    def path(self, path: str) -> str:
        return f"http://{self.address}/{path}"


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
        return block.hash()[:DIFFICULTY] == "0" * DIFFICULTY

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def pow(self, block: Block) -> int:
        while self.valid_pow(block) is False:
            block.header.nonce = random.randint(0, 2**64)
            block.header.timestamp = time()
        return block.header.nonce

    def new_transaction(
        self, sender: Wallet, recipient: str, amount: float, time=time()
    ) -> Transaction:
        transaction = Transaction(sender, recipient, amount, time)
        self.transactions.append(transaction)
        return transaction

    def new_block(
        self, nonce: int, index=None, previous_hash=None, time=time()
    ) -> Block:
        header = BlockHeader(
            time,
            previous_hash or self.hash(self.chain[-1]),
            index or self.chain[-1].header.index + 1,
            nonce,
        )
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
            for tx in block.transactions:
                if not tx.signature:
                    return False
                if not Wallet().verify(tx.hash(), tx.signature):
                    return False
            prev_block = block
        return True

    def register_node(self, address):
        if isinstance(address, str):
            address = Node(address)
        self.nodes.add(address)

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None  # 가장 긴 체인
        longest = len(self.chain)  # 가장 긴 체인 길이
        for node in neighbours:  # 모든 이웃 노드에 대해 체인 길이를 비교
            response = requests.get(node.path("chain"))
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                chain = [Block.from_dict(block) for block in chain]
                if length > longest and self.valid_chain(
                    chain
                ):  # 길이가 더 길고 유효한 체인이라면
                    longest = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False
