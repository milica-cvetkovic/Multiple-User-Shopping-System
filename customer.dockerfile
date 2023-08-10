FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applications/

COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/customer.py ./customer.py
COPY applications/requirements.txt ./requirements.txt
COPY applications/keys.json ./keys.json

RUN mkdir -p /opt/src/applications/solidity
RUN mkdir -p /opt/src/applications/solidity/output

COPY applications/solidity/contract.sol ./solidity/contract.sol
COPY applications/solidity/output/Contract.abi ./solidity/output/Contract.abi
COPY applications/solidity/output/Contract.bin ./solidity/output/Contract.bin

RUN pip install pymysql
RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "./customer.py" ]