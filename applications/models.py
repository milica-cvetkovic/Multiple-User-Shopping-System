from flask_sqlalchemy import SQLAlchemy;
from flask_migrate import Migrate;

database = SQLAlchemy ();
migrate = Migrate();

class ProductCategory(database.Model):
    __tablename__="productcategory";

    id = database.Column(database.Integer, primary_key=True);
    productId = database.Column(database.Integer, database.ForeignKey("product.id"), nullable=False);
    categoryId = database.Column(database.Integer, database.ForeignKey("category.id"), nullable=False);

class ProductInOrder(database.Model):
    __tablename__ = "productinorder";

    id = database.Column(database.Integer, primary_key=True);
    quantity = database.Column(database.Integer);
    productId = database.Column(database.Integer, database.ForeignKey("product.id"), nullable=False);
    orderId = database.Column(database.Integer, database.ForeignKey("order.id"), nullable=False);

class Category(database.Model):
    __tablename__="category";

    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);

    productsCategory = database.relationship("Product", secondary=ProductCategory.__table__, back_populates="categoriesProduct");

class Product(database.Model):
    __tablename__="product";

    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), unique=True, nullable=False);
    price = database.Column(database.Double, nullable=False);

    categoriesProduct = database.relationship("Category", secondary=ProductCategory.__table__, back_populates ="productsCategory");
    orders = database.relationship("Order", secondary=ProductInOrder.__table__, back_populates="productsOrder");


class Order(database.Model):
    __tablename__="order";

    id = database.Column(database.Integer, primary_key=True);
    amount = database.Column(database.Double, nullable=False);
    status = database.Column(database.String(256), nullable=False);
    dateCreated = database.Column(database.Date, nullable=False);
    email = database.Column(database.String(256), nullable=False);
    address = database.Column(database.String(256));

    productsOrder = database.relationship("Product", secondary= ProductInOrder.__table__, back_populates = "orders");


