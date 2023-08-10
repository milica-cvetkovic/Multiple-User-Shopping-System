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
from validate_email import validate_email;
import re;

from configuration import Configuration

from models import database, User, UserRole;
from models import migrate

application = Flask ( __name__ )
application.config.from_object ( Configuration )

if( not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"]);

database.init_app ( application )
migrate.init_app ( application, database )

@application.route ( "/", methods = ["GET"] )
def hello_world ( ):
    return "<h1>Hello world!</h1>"

@application.route("/register_customer", methods = ["POST"])
def register_customer():

    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len (email) == 0;
    passwordEmpty = len(password) == 0;
    forenameEmpty = len(forename) == 0;
    surnameEmpty = len(surname) == 0;

    if (forenameEmpty):
        return jsonify(message="Field {} is missing.".format("forename")), 400;
    if (surnameEmpty):
        return jsonify(message="Field {} is missing.".format("surname")), 400;
    if(emailEmpty):
        return jsonify(message="Field {} is missing.".format("email")), 400;
    if (passwordEmpty):
        return jsonify(message="Field {} is missing.".format("password")), 400

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b';
    result = re.match(regex, email);

    if(not result):
        return jsonify(message="Invalid email."), 400;

    if(len(password) < 8):
        return jsonify(message="Invalid password."), 400;

    check_email = User.query.filter(User.email == email).all();

    if(len(check_email ) != 0):
        return jsonify(message="Email already exists."), 400;

    user = User(email= email, password = password, forename = forename, surname = surname);
    database.session.add(user);
    database.session.commit();

    user_role = UserRole (userId = user.id, roleId = 1);
    database.session.add(user_role);
    database.session.commit();

    return Response(status=200);


@application.route("/register_courier", methods=["POST"])
def register_courier():
    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;
    forenameEmpty = len(forename) == 0;
    surnameEmpty = len(surname) == 0;

    if (forenameEmpty):
        return jsonify(message="Field {} is missing.".format("forename")), 400;
    if (surnameEmpty):
        return jsonify(message="Field {} is missing.".format("surname")), 400;
    if (emailEmpty):
        return jsonify(message="Field {} is missing.".format("email")), 400;
    if (passwordEmpty):
        return jsonify(message="Field {} is missing.".format("password")), 400

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b';
    result = re.match(regex, email);

    if (not result):
        return jsonify(message="Invalid email."), 400;

    if (len(password) < 8):
        return jsonify(message="Invalid password."), 400;

    check_email = User.query.filter(User.email == email).all();

    if (len(check_email) != 0):
        return jsonify(message="Email already exists."), 400;

    user = User(email=email, password=password, forename=forename, surname=surname);
    database.session.add(user);
    database.session.commit();

    user_role = UserRole(userId=user.id, roleId=2);
    database.session.add(user_role);
    database.session.commit();

    return Response(status=200);

jwt = JWTManager(application)

@application.route("/login", methods=["POST"])
def login():

    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;

    if (emailEmpty):
        return jsonify(message="Field {} is missing.".format("email")), 400;
    if (passwordEmpty):
        return jsonify(message="Field {} is missing.".format("password")), 400;

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b';
    result = re.match(regex, email);

    if (not result):
        return jsonify(message="Invalid email."), 400;

    user = User.query.filter(User.email == email, User.password == password ).first();

    if( not user ):
        return jsonify(message="Invalid credentials."), 400;

    additional_claim = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "roles": [str(role) for role in user.roles]
    }

    access_token = create_access_token(identity=user.email, additional_claims=additional_claim);
    refresh_token = create_refresh_token(identity=user.email, additional_claims=additional_claim);

    return jsonify(accessToken = access_token), 200;

@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():

    claims = get_jwt();

    if( not claims):
        return jsonify(msg="Missing Authorization Header"), 401;

    email = claims["email"];

    user = User.query.filter(User.email == email).first();

    if( not user):
        return jsonify(message="Unknown user."), 400;

    delete_user = User.query.filter(User.email == email).first();
    database.session.delete(delete_user);
    database.session.commit();

    return Response(status=200);


import os
if ( __name__ == "__main__" ):
    HOST = "0.0.0.0" if ( "DATABASE_URL" in os.environ ) else "127.0.0.1"
    application.run ( debug = True, host = HOST, port=5000 )