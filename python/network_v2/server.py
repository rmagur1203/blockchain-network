if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

    from variables import port, node_id
else:
    from .variables import port, node_id

import json
from flask import Flask

import logging

print(f"Node ID: {node_id}")
print(f"Port: {port}")

app = Flask(__name__)

logging.getLogger("werkzeug").disabled = True

with app.app_context():
    from routes import nodes, transactions, chain, api

    app.register_blueprint(nodes.route)
    app.register_blueprint(transactions.route)
    app.register_blueprint(chain.route)
    app.register_blueprint(api.route)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
