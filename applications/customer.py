import csv
import io
import os;

from ethpm.tools.builder import contract_type
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

@application.route("/search", methods=["GET"])
@role_check(role="customer")
def search():

    product_name = request.args.get("name", "");
    category_name = request.args.get("category","");

    result = {
        "categories":[],
        "products":[]
    };

    if(len(product_name)== 0 and len(category_name) == 0 ):
        result["products"] = Product.query;
        result["categories"] = Category.query;
    elif (len(product_name) == 0):
        result["categories"] = Category.query.filter(Category.name.like(f"%{category_name}"));
        result["products"] = Product.query.join(ProductCategory).join(Category).filter(Category.name.like(f"%{category_name}%"));
    elif(len(category_name) == 0):
        result["products"] = Product.query.filter(Product.name.like(f"%{product_name}%"));
        result["categories"] = Category.query.join(ProductCategory).join(Product).filter(Product.name.like(f"%{product_name}%"));
    else:
        result["products"] = Product.query.filter(Product.name.like(f"%{product_name}%"));
        result["categories"] = Category.query.filter(Category.name.like(f"%{category_name}%")).join(ProductCategory).join(Product).filter(Product.name.like(f"%{product_name}%"));



    result["products"] = result["products"].all();
    result["categories"] = result["categories"].all();



    result = {
        "categories":[category.name for category in result["categories"]],
        "products": [

            {
                "categories": [category.name for category in product.categoriesProduct],
                "id":product.id,
                "name":product.name,
                "price":product.price
            }
            for product in result["products"]
        ]
    };

    return Response(json.dumps(result), status=200);

@application.route("/order", methods=["POST"])
@role_check(role="customer")
def order():

    requests = request.json.get("requests","");
    address = request.json.get("address","");

    if(len(requests) == 0):
        return jsonify(message="Field requests is missing."), 400;

    products = [];
    quantities = [];
    amount = 0;

    for i in range (len(requests)):
        id = requests[i].get("id","");
        quantity = requests[i].get("quantity","");

        if(id == ""):
            return jsonify(message=f"Product id is missing for request number {i}."), 400;
        if(quantity == ""):
            return jsonify(message=f"Product quantity is missing for request number {i}."), 400;

        try:
            int(id);
        except:
            return jsonify(message=f"Invalid product id for request number {i}."), 400;

        id = int(id);

        if(id <= 0):
            return jsonify(message=f"Invalid product id for request number {i}."), 400;

        try:
            int(quantity);
        except:
            return jsonify(message=f"Invalid product quantity for request number {i}."), 400;

        quantity = int(quantity);

        if(quantity <= 0):
            return jsonify(message=f"Invalid product quantity for request number {i}."), 400;

        product = Product.query.filter(Product.id == id).first();

        if(not product):
            return jsonify(message=f"Invalid product for request number {i}."), 400;

        products.append(product);
        quantities.append(quantity);
        amount+=product.price*quantity;

    if (len(address) == 0):
        return jsonify(message="Field address is missing."), 400;

    if (not web3.is_address(address)):
        return jsonify(message="Invalid address."), 400;

    verify_jwt_in_request();
    claims = get_jwt();
    email = claims["email"];

    order = Order(amount=amount, status="CREATED", dateCreated=datetime.now(), email=email);

    database.session.add(order);
    database.session.commit();

    j = 0;
    for p in products:
        product_order = ProductInOrder(productId=p.id, orderId = order.id, quantity=quantities[j]);
        database.session.add(product_order);
        database.session.commit();
        j+=1;

    keys = json.loads(read_file("keys.json"))

    customer = web3.to_checksum_address(keys["address"])
    private_key = Account.decrypt(keys, "iep_project").hex ( );

    bytecode = read_file("./solidity/output/Contract.bin")
    abi = read_file("./solidity/output/Contract.abi");

    contract = web3.eth.contract(bytecode=bytecode, abi=abi);

    owner = web3.eth.accounts[0];

    transaction_hash = contract.constructor((int)(amount), owner, customer).transact({
        "from": owner
    })

    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash);
    contract_address = receipt.contractAddress;

    order.address = contract_address;

    database.session.add(order);
    database.session.commit();

    return jsonify(id=order.id), 200;

@application.route("/status", methods=["GET"])
@role_check(role="customer")
def status():

    verify_jwt_in_request();
    claims = get_jwt();
    email = claims["email"];

    orders = Order.query.filter(Order.email == email).all();

    results = {
        "orders": [
            {
                "products": [
                    {
                        "categories": [category.name for category in product.categoriesProduct],
                        "name": product.name,
                        "price": product.price,
                        "quantity": ProductInOrder.query.filter(ProductInOrder.productId == product.id, ProductInOrder.orderId == order.id).first().quantity
                    }
                    for product in Product.query.join(ProductInOrder).filter(ProductInOrder.orderId == order.id).all()
                ],
                "price": order.amount,
                "status": order.status,
                "timestamp": order.dateCreated.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            for order in orders
        ]
    }

    return Response(json.dumps(results), status=200);

@application.route("/delivered", methods=["POST"])
@role_check(role="customer")
def delivered():

    id = request.json.get("id", "");
    keys = request.json.get("keys", "");
    passphrase = request.json.get("passphrase", "");

    if(id == ""):
        return jsonify(message="Missing order id."), 400;

    try:
        int(id);
    except:
        return jsonify(message="Invalid order id."), 400;

    id = int(id);

# je l dobro ovo
    if(id <= 0):
        return jsonify(message="Invalid order id."), 400;

    order = Order.query.filter(Order.id == id).first();

    if(not order):
        return jsonify(message="Invalid order id."), 400;

    if(order.status != "PENDING"):
        return jsonify(message="Invalid order id."), 400;

    if (len(keys) == 0):
        return jsonify(message="Missing keys."), 400;

    if (len(passphrase) == 0):
        return jsonify(message="Missing passphrase."), 400;

    keys = keys.replace("\'", "\"")
    keys = json.loads(keys);

    try:
        private_key = Account.decrypt(keys, passphrase).hex();
    except:
        return jsonify(message="Invalid credentials."), 400;

    customer = web3.to_checksum_address(keys["address"]);

    contract_address = order.address;

    abi = read_file("./solidity/output/Contract.abi");

    contract = web3.eth.contract(address=contract_address, abi=abi);

    customer_contract = contract.functions.get_customer().call();

    if(customer != customer_contract):
        return jsonify(message="Invalid customer account."), 400;

    if (not contract.functions.get_paid().call()):
        return jsonify(message="Transfer not complete."), 400;

    if( not contract.functions.get_courier_set().call()):
        return jsonify(message="Delivery not complete."), 400;

    try:

        transaction = contract.functions.transfer_money_to_owner_and_courier().build_transaction({
            "from": customer,
            "nonce": web3.eth.get_transaction_count(customer),
            "gasPrice": web3.eth.gas_price
        })

        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    except ContractLogicError as error:
        if (error == "First"):
            return jsonify(message="Transfer not complete."), 400;
        if (error == "Second"):
            return jsonify(message="Delivery not complete."), 400;

    order.status ="COMPLETE";
    database.session.add(order);
    database.session.commit();

    return Response(status=200);

@application.route("/pay", methods=["POST"])
@role_check(role="customer")
def pay():
    id = request.json.get("id", "");
    keys = request.json.get("keys", "");
    passphrase = request.json.get("passphrase", "");

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

    #if (order.status != "PENDING"):
    #    return jsonify(message="Invalid order id."), 400;

    if (len(keys) == 0):
        return jsonify(message="Missing keys."), 400;

    if (len(passphrase) == 0):
        return jsonify(message="Missing passphrase."), 400;

    keys = json.loads(keys);

    try:
        private_key = Account.decrypt(keys, passphrase).hex();
    except:
        return jsonify(message="Invalid credentials."), 400;

    customer = web3.to_checksum_address(keys["address"]);

    order = Order.query.filter(Order.id == id).first();

    contract_address = order.address;

    abi = read_file("./solidity/output/Contract.abi");

    contract = web3.eth.contract(address=contract_address, abi=abi);

    balance = web3.eth.get_balance (customer);

    if (balance < order.amount):
        return jsonify(message=f"Insufficient funds."), 400;

    try:
        #transaction_hash = contract.functions.pay().transact({
        #    "from": customer,
        #    "value": (int)(order.amount)
        #});

        transaction = contract.functions.pay().build_transaction({
            "from": customer,
            "value": (int)(order.amount),
            "nonce": web3.eth.get_transaction_count(customer),
            "gasPrice": web3.eth.gas_price
        })

        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    except ContractLogicError as error:
        return jsonify(message="Transfer already complete."), 400;

    return Response(status=200);

import os
if ( __name__ == "__main__" ):
    HOST = "0.0.0.0" if ( "DATABASE_URL" in os.environ ) else "127.0.0.1"
    application.run ( debug = True, host = HOST, port=5002 )