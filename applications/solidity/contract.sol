pragma solidity ^0.8.2;

contract Contract {

    address payable customer;
    address payable owner;
    address payable courier;
    uint256 amount;
    uint courier_set;
    uint paid;

    constructor ( uint256 _amount, address payable _owner, address payable _customer ) {
        owner = _owner;
        customer = _customer;
        amount = _amount;
        courier_set = 0;
        paid = 0;
    }

    modifier only_customer(){
        require(msg.sender == customer);
        _;
    }

    function pay() public payable only_customer {
        require(paid == 0, "Transfer already complete.");
        paid = 1;
    }

    function get_customer() public view returns ( address ) {
        return customer;
    }

    function get_owner() public view returns ( address) {
        return owner;
    }

    function get_paid() public view returns (bool) {
        return paid == 1;
    }

    function get_courier_set() public view returns (bool) {
        return courier_set == 1;
    }

    function transfer_money_to_owner_and_courier() public payable only_customer {
        //require(paid == 1, "First");
        //require(courier_set == 1, "Second");
        owner.transfer(uint((amount*80)/100));
        courier.transfer(uint((amount*20)/100));
    }

    function add_courier(address payable _courier) public {
        require(paid == 1, "Error");
        courier = _courier;
        courier_set = 1;
    }

}