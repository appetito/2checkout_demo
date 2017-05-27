from __future__ import print_function
# import twocheckout2 as tco
import twocheckout3 as tco
import json

from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify

import decimal
import os
import uuid
from os.path import join, dirname
from dotenv import load_dotenv


app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app.secret_key = os.environ.get('APP_SECRET_KEY')

TCO_PUBLIC_KEY = os.environ.get('TCO_PUBLIC_KEY')
TCO_PRIVATE_KEY = os.environ.get('TCO_PRIVATE_KEY')
TCO_SELLER_ID = os.environ.get('TCO_SELLER_ID')
TCO_LOGIN = os.environ.get("TCO_LOGIN")
TCO_PASSWORD = os.environ.get("TCO_PASSWORD")


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('new_checkout'))


@app.route('/checkouts/new', methods=['GET'])
def new_checkout():
    return render_template('checkouts/new.html', seller_id=TCO_SELLER_ID, public_key=TCO_PUBLIC_KEY)


@app.route('/checkouts/<status>/<tx_id>', methods=['GET'])
def show_checkout(status, tx_id):
    if status == 'ok':
        result = {
            'header': 'Sweet Success!',
            'icon': 'success',
            'message': ('Your test transaction has been successfully processed.'
                        'See the API response and try again.')
        }
        error = None
    else:
        error = session.get("error")
        error_raw = session.get("error")
        result = {
            'header': 'Transaction Failed',
            'icon': 'fail',
            'message': ('Your test transaction has a error  <b>{}</b>. See'
                        ' API response and try again.').format(error)
        }

    sale = None
    error_raw = session.get("error_raw")
    response = json.loads(session.get("sale"))
    return render_template('checkouts/show.html', sale=sale, response=response, error=error,
                           error_raw=error_raw, result=result)


@app.route('/checkouts', methods=['POST'])
def create_checkout():
    curr = request.form['currency']
    price_key = 'price_' + curr
    price = decimal.Decimal(request.form[price_key])
    tx_amount = int(request.form['amount']) * price
    tco.Api.auth_credentials({
        'private_key': TCO_PRIVATE_KEY,
        'seller_id': TCO_SELLER_ID,
        'mode': 'sandbox'
    })

    params = {
        'merchantOrderId': str(uuid.uuid4()),
        'token': request.form["tco_token"],
        'currency': curr,
        'total': str(tx_amount),
        'currency': 'USD',
        'billingAddr': {
            'name': 'Testing Tester',
            'addrLine1': '123 Test St',
            'city': 'Columbus',
            'state': 'OH',
            'zipCode': '43123',
            'country': 'USA',
            'email': 'example@2co.com',
            'phoneNumber': '555-555-5555'
        }
    }

    try:
        result = tco.Charge.authorize(params)
        session["error"] = ""
        session["error_raw"] = ""
        session["sale"] = json.dumps(result)
        return redirect(url_for('show_checkout', status='ok', tx_id=result.transactionId))
    except tco.TwocheckoutError as error:
        session["error"] = "{} {}".format(error.code, error.msg)
        session["error_raw"] = error.raw
        session["sale"] = "{}"
        return redirect(url_for('show_checkout', status='err', tx_id='xxx'))


@app.route('/refund/partial', methods=['POST'])
def refund_partial():
    params = {
        'sale_id': request.form["tx_id"],
        'category': 5,
        'comment': "Refunding Sale. Partial",
        'amount': request.form["amount"],
        'currency': 'customer',
    }

    tco.Api.credentials({
        'username': TCO_LOGIN,
        'password': TCO_PASSWORD,
        'mode': 'sandbox'
    })

    try:
        sale = tco.Sale.find({'sale_id': request.form["tx_id"]})
        invoice = sale.invoices[0]
        result = invoice.refund(params)
        return jsonify(result)
    except tco.TwocheckoutError as error:
        return "Error: {} {}".format(error.code, error.msg)


@app.route('/refund', methods=['POST'])
def refund():
    params = {
        'sale_id': request.form["tx_id"],
        'category': 5,
        'comment': "Refunding Sale"
    }

    tco.Api.credentials({
        'username': TCO_LOGIN,
        'password': TCO_PASSWORD,
        'mode': 'sandbox'
    })

    try:
        sale = tco.Sale.find({'sale_id': request.form["tx_id"]})
        invoice = sale.invoices[0]
        result = invoice.refund(params)
        return jsonify(result)
    except tco.TwocheckoutError as error:
        return "Error: {} {}".format(error.code, error.msg)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4567, debug=True)
