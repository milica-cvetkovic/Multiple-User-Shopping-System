import csv
import io

from flask import Flask, request, Response,jsonify, json;
from flask import request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func
import pymysql;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, get_jwt_header, verify_jwt_in_request;
from sqlalchemy import and_;
from sqlalchemy_utils import database_exists, create_database;
import re;
from datetime import datetime;
from functools import wraps;

from configuration import Configuration;

from models import *;

from web3 import Web3
from web3 import HTTPProvider
from web3 import Account
from web3.exceptions import ContractLogicError
from web3.exceptions import ContractCustomError

application = Flask ( __name__ )
application.config.from_object ( Configuration )

database.init_app ( application )
migrate.init_app ( application, database )

jwt = JWTManager(application);

web3 = Web3 ( HTTPProvider ( "http://ganache:8545" ) )

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

def role_check(role):
    def decorator(function):
        @jwt_required()
        @wraps(function)
        def wrapper(*args, **kwargs):
            claims = get_jwt();
            if("roles" in claims) and (role in claims["roles"]):
                return function(*args,**kwargs);
            else:
                return jsonify(msg="Missing Authorization Header"), 401;
        return wrapper;
    return decorator;

@application.route ( "/", methods = ["GET"] )
def hello_world ( ):
    return "<h1>Hello world!</h1>"

@application.route("/orders_to_deliver", methods=["GET"])
@role_check(role="courier")
def orders_to_deliver():

    orders = Order.query.filter(Order.status == "CREATED").all();

    results = {
        "orders": [
            {
                "id":order.id,
                "email":order.email
            }
            for order in orders
        ]
    }

    return Response(json.dumps(results), status=200);

@application.route("/pick_up_order", methods=["POST"])
@role_check(role="courier")
def pick_up_order():

    id = request.json.get("id","");
    address = request.json.get("address","");

    if (id == ""):
        return jsonify(message="Missing order id."), 400;

    try:
        int(id);
    except:
        return jsonify(message="Invalid order id."), 400;

    id = int(id);

    # je l dobro ovo
    if (id <= 0):
        return jsonify(message="Invalid order id."), 400;

    order = Order.query.filter(Order.id == id).first();

    if (not order):
        return jsonify(message="Invalid order id."), 400;

    if (order.status == "COMPLETE" or order.status == "PENDING"):
        return jsonify(message="Invalid order id."), 400;

    if(len(address) == 0):
        return jsonify(message="Missing address."), 400;

    if (not web3.is_address(address)):
        return jsonify(message="Invalid address."), 400;

    contract_address = order.address;

    abi = read_file("./solidity/output/Contract.abi");

    contract = web3.eth.contract(address=contract_address, abi=abi);

    owner = web3.eth.accounts[0];

    address  = web3.to_checksum_address(address);

    try:
         transaction_hash = contract.functions.add_courier(address).transact({
            "from": owner
         });

    except ContractLogicError as error:
        return jsonify(message="Transfer not complete."), 400;

    order.status = "PENDING";
    database.session.add(order);
    database.session.commit();

    return Response(status=200);

import os
if ( __name__ == "__main__" ):
    HOST = "0.0.0.0" if ( "DATABASE_URL" in os.environ ) else "127.0.0.1"
    application.run ( debug = True, host = HOST, port=5003 )