from core import Blockchain
from util import is_port_in_use

blockchain = Blockchain()
port = 5000

while is_port_in_use(port):
    port += 1

node_id = f'node_{port}'
mine_owner = 'master'
mine_profit = 0.1