from pyspark.sql import SparkSession
from pyspark.sql.functions import col;

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

#result = spark.sql(
#    "select c.name, case when (select coalesce(sum(po1.quantity),0) as delivered from category c1 join productcategory pc1 on c1.id=pc1.categoryId join productinorder po1 on pc1.productId=po1.productId join order o1 on po1.orderId=o1.id where o1.status='COMPLETE' and c1.name = c.name group by c1.name)>0 then (select coalesce(sum(po1.quantity),0) as delivered from category c1 join productcategory pc1 on c1.id=pc1.categoryId join productinorder po1 on pc1.productId=po1.productId join order o1 on po1.orderId=o1.id where o1.status='COMPLETE' and c1.name = c.name group by c1.name) else (select 0 from category c1 join productcategory pc1 on c1.id=pc1.categoryId join productinorder po1 on pc1.productId=po1.productId join order o1 on po1.orderId=o1.id where c1.name not in (select coalesce(sum(po2.quantity),0) as delivered from category c2 join productcategory pc2 on c2.id=pc2.categoryId join productinorder po2 on pc2.productId=po2.productId join order o2 on po2.orderId=o2.id where o2.status='COMPLETE' and group by c1.name) and c1.name=c.name group by c1.name) end from category c join productcategory on c.id=productcategory.categoryId join po on productcategory.productId=po.productId join order on po.orderId= order.id group by c.name order by coalesce(sum(po.quantity),0) desc, c.name asc"
#   ).toJSON().collect();

result1 = spark.sql("select category.name as name, coalesce(sum(productinorder.quantity), 0) as delivered from category join productcategory on category.id=productcategory.categoryId join productinorder on productcategory.productId=productinorder.productId join order on productinorder.orderId= order.id where order.status='COMPLETE' group by category.name");

result2 = spark.sql("select c.name as name, 0 as delivered from category c where c.name not in ( select c1.name from category c1 join productcategory on c1.id=productcategory.categoryId join productinorder on productcategory.productId=productinorder.productId join order on productinorder.orderId= order.id where order.status='COMPLETE' group by c1.name)");

result = result1.union(result2).orderBy(col("delivered").desc(), col("name").asc()).toJSON().collect();

file = open("category_statistics.txt", "w");

for row in result:
    data = json.dumps(row);
    file.write(data);
    file.write("\n");

file.close();

print("start_collect" + str(result) + "end_collect");

spark.stop();