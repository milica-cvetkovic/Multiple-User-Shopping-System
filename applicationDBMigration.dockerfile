FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/migrate.py ./migrate.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install pymysql
RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "./migrate.py" ]