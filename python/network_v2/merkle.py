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
