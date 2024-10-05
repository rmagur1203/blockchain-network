import json
import os
from flask import Flask, render_template, request
import requests


app = Flask(__name__, template_folder=os.getcwd() + '/templates')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        contract_address = request.form.to_dict(flat=False)['smart_contract_address'][0]
        print(contract_address)

        # 블록 정보 호출
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        res = requests.get(f'http://localhost:5000/chain', headers=headers)
        res_json = json.loads(res.content)
        nft_TF = False

        for _block in res_json['chain']:
            for _tx in _block['transactions']:
                if _tx['contract'] is not None and\
                      _tx['contract']['address'] == contract_address:
                    exec(_tx['contract']['code'])
                    nft_TF = True
                    break
        if nft_TF:
            return render_template(
                "NFT_Wallet.html",
                nft_name=_tx['contract']['code'].split('"')[3],
                nft_img_url=_tx['contract']['code'].split('"')[7],
                nft_address=_tx['contract']['address']
            )
        else:
            return "잘못된 지갑주소입니다."
    return render_template("NFT_Wallet_login.html")

if __name__ == '__main__':
    app.run(host='localhost', port=8082)
