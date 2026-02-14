#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
import threading
import webbrowser

sys.path.insert(0, str(Path(__file__).parent))

from controllers.fortress_controller import FortressController
from controllers.velocity_controller import VelocityController
from controllers.core_vault_controller import CoreVaultController
from controllers.time_capsule_controller import TimeCapsuleController
from controllers.net_shield_controller import NetShieldController

app = Flask(__name__, static_folder='ui')

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('ui', path)

@app.route('/api/fortress/execute', methods=['POST'])
def fortress_execute():
    controller = FortressController()
    return jsonify(controller.execute())

@app.route('/api/velocity/execute', methods=['POST'])
def velocity_execute():
    controller = VelocityController()
    return jsonify(controller.execute())

@app.route('/api/core-vault/execute', methods=['POST'])
def core_vault_execute():
    controller = CoreVaultController()
    return jsonify(controller.execute())

@app.route('/api/time-capsule/execute', methods=['POST'])
def time_capsule_execute():
    controller = TimeCapsuleController()
    return jsonify(controller.execute())

@app.route('/api/net-shield/execute', methods=['POST'])
def net_shield_execute():
    controller = NetShieldController()
    return jsonify(controller.execute())

def main():
    print("="*60)
    print("KNOUX OS Guardian - Starting UI")
    print("="*60)
    
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    sys.exit(main())
