from pyspark.sql import SparkSession

import os;
import re;

from flask import json;

DATABASE_URL = os.environ["DATABASE_URL"];

builder = SparkSession.builder.appName ( "PySpark Database" );

spark = builder.getOrCreate();

products = spark.read.format("jdbc").option("driver","com.mysql.cj.jdbc.Driver").option("url",f"jdbc:mysql://{DATABASE_URL}:3306/database").option("dbtable","database.product").option("user","root").option("password","root").load();

categories = spark.read.format("jdbc").option("driver","com.mysql.cj.jdbc.Driver").option("url",f"jdbc:mysql://{DATABASE_URL}:3306/database").option("dbtable","database.category").option("user","root").option("password","root").load();

productcategory = spark.read.format("jdbc").option("driver","com.mysql.cj.jdbc.Driver").option("url",f"jdbc:mysql://{DATABASE_URL}:3306/database").option("dbtable","database.productcategory").option("user","root").option("password","root").load();

productsorder = spark.read.format("jdbc").option("driver","com.mysql.cj.jdbc.Driver").option("url",f"jdbc:mysql://{DATABASE_URL}:3306/database").option("dbtable","database.productinorder").option("user","root").option("password","root").load();

orders = spark.read.format("jdbc").option("driver","com.mysql.cj.jdbc.Driver").option("url",f"jdbc:mysql://{DATABASE_URL}:3306/database").option("dbtable","database.order").option("user","root").option("password","root").load();

products.createOrReplaceTempView("product");
categories.createOrReplaceTempView("category");
productcategory.createOrReplaceTempView("productcategory");
productsorder.createOrReplaceTempView("productinorder");
orders.createOrReplaceTempView("order");

# sa uslovom
# "select P.name, (select sum(PO1.quantity) from product P1 join productinorder PO1 on P1.id=PO1.productId join order O1 on O1.id=PO1.orderId where O1.status='COMPLETE' and P.name=P1.name) as sold, coalesce((select sum(PO2.quantity) from product P2 join productinorder PO2 on P2.id=PO2.productId join order O2 on O2.id=PO2.orderId  where O2.status!='COMPLETE' and P.name=P2.name),0) as waiting  from product P where coalesce((select sum(PO3.quantity) from product P3 join productinorder PO3 on P3.id=PO3.productId join order O3 on O3.id=PO3.orderId where O3.status='COMPLETE' and P.name=P3.name),0)>0"

result = spark.sql(
    "select P.name, coalesce((select sum(PO1.quantity) from product P1 join productinorder PO1 on P1.id=PO1.productId join order O1 on O1.id=PO1.orderId where O1.status='COMPLETE' and P.name=P1.name),0) as sold, coalesce((select sum(PO2.quantity) from product P2 join productinorder PO2 on P2.id=PO2.productId join order O2 on O2.id=PO2.orderId  where O2.status!='COMPLETE' and P.name=P2.name),0) as waiting  from product P where coalesce((select sum(PO3.quantity) from product P3 join productinorder PO3 on P3.id=PO3.productId join order O3 on O3.id=PO3.orderId where O3.status='COMPLETE' and P.name=P3.name),0)>0 or coalesce((select sum(PO2.quantity) from product P2 join productinorder PO2 on P2.id=PO2.productId join order O2 on O2.id=PO2.orderId  where O2.status!='COMPLETE' and P.name=P2.name),0) > 0"
).toJSON().collect();

file = open("product_statistics.txt", "w");

for row in result:
    data = json.dumps(row);
    file.write(data);
    file.write("\n");

file.close();

print("start_collect" + str(result) + "end_collect");

spark.stop();