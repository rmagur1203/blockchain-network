from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime
import requests
import json
import os
import pandas as pd
import random

app = Flask(__name__, template_folder=os.getcwd())
node_port_list = ['5000', '5001', '5002']

@app.route('/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		print("login 버튼을 누름")
		input_value = request.form.to_dict(flat=False)
		print("login 지갑주소 : ", input_value)
		# 노드 주소 랜덤 선정
		node_id = random.choice(node_port_list)
		# 기존 user 정보 확인
		headers = {'Content-Type': 'application/json; charset=utf-8'}
		# 선정된 노드 주소로 데이터 요청
		res = requests.get("http://localhost:" + node_id + "/chain", headers=headers)
		status_json = json.loads(res.text)
		tx_amount_l = []
		tx_sender_l = []
		tx_reciv_l = []
		tx_time_l = []
		for chain_index in range(len(status_json['chain'])):
			chain_tx = status_json['chain'][chain_index]['transactions']
			for each_tx in range(len(chain_tx)):
				tx_amount_l.append(chain_tx[each_tx]['amount'])
				tx_sender_l.append(chain_tx[each_tx]['sender'])
				tx_reciv_l.append(chain_tx[each_tx]['recipient'])
				tx_time_l.append(chain_tx[each_tx]['timestamp'])
		df_tx = pd.DataFrame()
		df_tx['timestamp'] = tx_time_l
		df_tx['sender'] = tx_sender_l
		df_tx['recipient'] = tx_reciv_l
		df_tx['amount'] = tx_amount_l
		df_sended = pd.DataFrame(df_tx.groupby('sender')['amount'].sum()).reset_index()
		df_sended.columns = ['user', 'sended_amount']
		df_received = pd.DataFrame(df_tx.groupby('recipient')['amount'].sum()).reset_index()
		df_received.columns = ['user', 'received_amount']
		df_status = pd.merge(df_received, df_sended, on='user', how='outer').fillna(0)
		df_status['balance'] = df_status['received_amount'] - df_status['sended_amount']
		if (df_status['user'] == input_value['wallet_id'][0]).sum() == 1:
			print("로그인성공")
			return render_template("wallet.html", wallet_id=input_value['wallet_id'][0], wallet_value=df_status[df_status['user'] == input_value['wallet_id'][0]]['balance'].iloc[0])
		else:
			return "잘못된 지갑주소입니다."
	return render_template('www/login.html')

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
	if request.method == 'POST':
		send_value = int(request.form.to_dict(flat=False)['send_value'][0])
		send_target = request.form.to_dict(flat=False)['send_target'][0]
		send_from = request.form.to_dict(flat=False)['send_from'][0]
		if send_value > 0:
			print(send_value)
			# transaction 입력하기
			headers = {'Content-Type': 'application/json; charset=utf-8'}
			# 노드 주소 랜덤 선정
			node_id = random.choice(node_port_list)
			data = {
				"sender": send_from,
				"recipient": send_target,
				"amount": send_value,
			}
			# 선정된 노드 주소로 데이터 요청
			requests.post("http://localhost:" + node_id + "/transactions/new", headers=headers, data=json.dumps(data)).content
			return "전송 완료!"
		else:
			return "0 pyBTC 이상 보내주세요!"
	return render_template('www/wallet.html')

app.run(port=8081)