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
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, get_jwt_header;
from sqlalchemy import and_;
from sqlalchemy_utils import database_exists, create_database;
import re;
from functools import wraps;

from configuration import Configuration;

from models import database, Product, Category, ProductCategory;
from models import migrate;

application = Flask ( __name__ )
application.config.from_object ( Configuration )

if( not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"]);

database.init_app ( application )
migrate.init_app ( application, database )

jwt = JWTManager(application);

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



@application.route("/update", methods = ["POST"])
@role_check(role="owner")
def update():

    file = request.files.get("file", None);
    if(not file):
        return jsonify(message="Field file is missing."), 400;


    content = request.files["file"].stream.read ( ).decode ( );

    products = [];
    products_set = set();
    i = 0;

    for line in content.split("\n"):

        row = line.split(",");

        if ( len(row) != 3):
            return jsonify(message=f"Incorrect number of values on line {i}."), 400;

        try:
            float(row[2]);
        except:
            return jsonify(message=f"Incorrect price on line {i}."), 400;

        price = float(row[2]);
        if(price <= 0):
            return jsonify(message=f"Incorrect price on line {i}."), 400;

        product_check = Product.query.filter(Product.name == row[1]).first();

        if(product_check):
            return jsonify(message=f"Product {row[1]} already exists."), 400;

        if(row[1] in products_set):
            return jsonify(message=f"Product {row[1]} already exists."), 400;

        products_set.add(row[1]);

        i+=1;

    for line in content.split("\n"):
        row = line.split(",");

        product = Product(name=row[1], price=float(row[2]));
        database.session.add(product);
        database.session.commit();

        categories = [str(item) for item in row[0].split("|")];

        for category in categories:

            category_check = Category.query.filter(Category.name == category).first();

            if (not category_check):
                category_check = Category(name=category);
                database.session.add(category_check);
                database.session.commit();

            product_category = ProductCategory(productId=product.id, categoryId=category_check.id);
            database.session.add(product_category);
            database.session.commit();

    return Response(status=200);

import requests
import re

# (?<=start_collect\[)((.|\n)*)(?=\]end_collect)

@application.route("/product_statistics", methods = ["GET"])
@role_check(role="owner")
def product_statistics():
    result = requests.get("http://owner_spark:5004/product_statistics").content;
    #result = str(result, encoding='ascii', errors ="ignore");

    #regex = r'(?<=start_collect\[)((.|\n)*)(?=\]end_collect)';
    #result = re.match(regex, result);

    #regex = r'\'([^\']*)\'';
    #result = re.findall(regex,result);

    #resultJSON = {
    #    "statistics":[json.loads(item) for item in result]
    #};

    return Response(result, status=200);

@application.route("/category_statistics", methods = ["GET"])
@role_check(role="owner")
def category_statistics():
    result = requests.get("http://owner_spark:5004/category_statistics").content;

    return Response(result, status=200);



import os
if ( __name__ == "__main__" ):
    HOST = "0.0.0.0" if ( "DATABASE_URL" in os.environ ) else "127.0.0.1"
    application.run ( debug = True, host = HOST, port=5001 )