from flask import Flask, render_template, request, url_for, redirect
import db
import time
import sqs
import uuid
import json

app = Flask(__name__)
#cur = db.conn.cursor()

def check_asset():
    cur = db.conn.cursor()
    cur.execute("select asset from asset_table")
    asset = cur.fetchall()
    cur.close()
    return asset[0][0]

@app.route('/purchase/<item>', methods=['POST'])
def purchase(item):
    asset = check_asset()
    cur = db.conn.cursor()
    cur.execute("select price from item_table where item='{}'".format(item))
    price = cur.fetchall()[0][0]
   
    if asset >= price:
        asset = asset-price
        cur.execute("update asset_table set asset={}".format(asset))
        cur.execute("insert into receipt_table (item, price, data) select item, price, data from item_table where item='{}'".format(item))
        db.conn.commit()
        cur.close()
        return redirect(url_for('index'))
    else:
        cur.close()
        return "We don't have enough assets."


@app.route('/initialize_asset', methods=['POST'])
def initialize_asset():
    asset = 3000 
    cur = db.conn.cursor()
    cur.execute("update asset_table set asset={}".format(asset))
    cur.execute("delete from receipt_table")
    db.conn.commit()
    cur.close()
    return redirect(url_for('index'))

@app.route('/charge_cash/<cash>', methods=['POST'])
def charge_cash(cash):
    cash = int(cash)
    if cash==1 or cash==5 or cash==10:
        msg = {"charge_amount" : cash}
        message_body = json.dumps(msg)
        response = sqs.sqs_client.send_message(QueueUrl=sqs.sqs_queue_url, MessageBody=message_body)
        time.sleep(15)
        return redirect(url_for('index'))
    else:
        return "BAD Request!!"


@app.route('/charge', methods=['GET', 'POST'])
def charge():
    return render_template('charge.html')


@app.route('/receipt', methods=['GET'])
def receipt():
    cur = db.conn.cursor()
    cur.execute("select * from receipt_table")
    result = cur.fetchall()
    result = result[::-1]
    cur.close()
    return render_template('receipt.html', result=result)


@app.route('/', methods=['GET', 'POST'])
def index():
    cur = db.conn.cursor()
    db.conn.commit()
    cur.close()
    asset = check_asset()
    print(asset)
    return render_template('index.html', asset=asset)

def main():
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    main()

