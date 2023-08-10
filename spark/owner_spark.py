from flask import Flask, json;
from flask import request, Response;

application = Flask ( __name__ )

import os
import subprocess
import re;

@application.route("/", methods=["GET"])
def index():
    return "Hello world!";

@application.route("/product_statistics", methods=["GET"])
def product_statistics():

    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/product_statistics.py"

    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

    result = subprocess.check_output(["/template.sh"])

    result_file = open("product_statistics.txt", "r");
    result = result_file.readlines();

    resultJSON = {
        "statistics": [json.loads(json.loads(item)) for item in result]
    };

    return resultJSON

@application.route("/category_statistics", methods=["GET"])
def category_statistics():

    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/category_statistics.py"

    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

    result = subprocess.check_output(["/template.sh"])

    result_file = open("category_statistics.txt", "r");
    result = result_file.readlines();

    resultJSON = {
        "statistics": [json.loads(json.loads(item))["name"] for item in result]
    };
    return resultJSON


if ( __name__ == "__main__" ):
    HOST = "0.0.0.0" if ( "DATABASE_URL" in os.environ ) else "127.0.0.1"
    application.run ( debug = True, host = HOST, port=5004 )