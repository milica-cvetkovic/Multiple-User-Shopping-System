import pprint

from web3 import Web3
from web3 import HTTPProvider
from web3 import Account

import json

web3 = Web3 ( HTTPProvider ( "http://127.0.0.1:8545" ) )

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

keys = json.loads ( read_file ( "keys.json" ) )

#address     = web3.to_checksum_address ( keys["address"] )
#private_key = Account.decrypt ( keys, "iep_project" ).hex ( )

address = "0x342185cc601cAe134106ab52FE85B15DB3874eC2";
private_key = "0x851a07e954c3618d19d4c54ac4ee7a65b168b1fec52398069de9e0b1edf9c11e";

print ( address )
print ( private_key )

balance = web3.from_wei ( web3.eth.get_balance ( address ), "ether" )

number_of_blocks = web3.eth.block_number

preety_printer = pprint.PrettyPrinter ( )

for i in range ( number_of_blocks + 1 ):
    block = web3.eth.get_block ( i, True )

    preety_printer.pprint ( dict ( block ) )

    for transaction in block.transactions:

        preety_printer.pprint ( dict ( transaction ) )

print(balance)