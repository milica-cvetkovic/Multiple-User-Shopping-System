from flask import Flask;
from configuration import Configuration;
from flask_migrate import Migrate, init, migrate, upgrade;
from models import database, User, Role, UserRole;
from sqlalchemy_utils import database_exists, create_database;

application = Flask(__name__);
application.config.from_object(Configuration);

migrate_object = Migrate(application, database);

if( not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"]);

database.init_app(application);

with application.app_context() as context:
    init();
    migrate (message ="Production migration");
    upgrade();

    customer_role = Role (name = "customer");
    courier_role = Role(name = "courier");
    owner_role = Role(name="owner");

    database.session.add(customer_role);
    database.session.add(courier_role);
    database.session.add(owner_role);
    database.session.commit();

    # dodaj ownera
    owner = User(
        forename="Scrooge",
        surname="McDuck",
        email="onlymoney@gmail.com",
        password="evenmoremoney"
    );

    database.session.add(owner);
    database.session.commit();

    user_role = UserRole(userId=owner.id, roleId=owner_role.id);
    database.session.add(user_role);
    database.session.commit();


