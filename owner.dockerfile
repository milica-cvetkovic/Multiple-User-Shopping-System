FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applications/

COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/owner.py ./owner.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install pymysql
RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "./owner.py" ]