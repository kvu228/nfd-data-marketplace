from web3 import Web3
from provider import get_web3_provider
from json import loads, dumps

PROVIDER_CACHE: 'dict[str, Web3]' = dict()


def to_wei(amount: float, unit: str = "ether"):
    """
    Compatibility helper for web3.py v5/v6 differences.
    """
    if hasattr(Web3, "to_wei"):
        return Web3.to_wei(amount, unit)
    # web3.py v5
    return Web3.toWei(amount, unit)


def from_wei(value, unit: str = "ether"):
    """
    Compatibility helper for web3.py v5/v6 differences.
    """
    if hasattr(Web3, "from_wei"):
        return Web3.from_wei(value, unit)
    # web3.py v5
    return Web3.fromWei(value, unit)


def ContractDeployOnce(contract_name: str):
    def Decorator(F: callable):
        def NewDeploy(*args, **kwargs):
            contract_data = None
            try:
                f = open("contracts.json", "r")
                contract_data = loads(f.read())
                f.close()
            except:
                contract_data = dict()

            if contract_name not in contract_data:
                contract_data[contract_name] = F(*args, **kwargs)

            f = open("contracts.json", "w")
            f.write(dumps(contract_data))
            f.close()
            return contract_data[contract_name]
        return NewDeploy
    return Decorator


def get_web3_provider(endpoint):

    if endpoint not in PROVIDER_CACHE or not PROVIDER_CACHE[endpoint].isConnected():
        PROVIDER_CACHE[endpoint] = Web3(Web3.HTTPProvider(
            endpoint, request_kwargs={'verify': False}))
        # PROVIDER_CACHE[endpoint].eth.set_gas_price_strategy(medium_gas_price_strategy)
    return PROVIDER_CACHE[endpoint]


def get_abi(filename):

    abi_file = open(filename, "r")
    data = loads(abi_file.read())["abi"]
    abi_file.close()
    return data


def get_bytecode(filename):
    bytecode_file = open(filename, "r")
    data = loads(bytecode_file.read())["bytecode"]
    bytecode_file.close()
    return data


def get_market_abi():

    return get_abi("artifacts/contracts/AssetMarket.sol/AssetMarket.json")


def get_market_bytecode():

    return get_bytecode("artifacts/contracts/AssetMarket.sol/AssetMarket.json")


def get_factory_bytecode():

    return get_bytecode("artifacts/contracts/AssetAgreementFactory.sol/AssetAgreementFactory.json")


def get_factory_abi():

    return get_abi("artifacts/contracts/AssetAgreementFactory.sol/AssetAgreementFactory.json")


def get_agreement_abi():

    return get_abi("artifacts/contracts/AssetAgreement.sol/AssetAgreement.json")


def get_agreement_bytecode():
    return get_bytecode("artifacts/contracts/AssetAgreement.sol/AssetAgreement.json")


def get_agreement_erc1155_abi():
    return get_abi("artifacts/contracts/AssetAgreementERC1155.sol/AssetAgreement.json")


def get_agreement_erc1155_bytecode():
    return get_bytecode("artifacts/contracts/AssetAgreementERC1155.sol/AssetAgreement.json")


def get_Agreement_contract(endpoint: str, address: str, account: str):
    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account
    return w3.eth.contract(address=address, abi=get_agreement_abi())


def get_Agreement_ERC1155_contract(endpoint: str, address: str, account: str):
    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account
    return w3.eth.contract(address=address, abi=get_agreement_erc1155_abi())


def get_AssetFactory_contract(endpoint: str, address: str, account: str):
    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account
    return w3.eth.contract(address=address, abi=get_factory_abi())


def get_Market_contract(endpoint: str, address: str, account: str):

    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account

    return w3.eth.contract(address=address, abi=get_market_abi())


class Contract:

    PRIVATE_KEY: str = None
    W3_PROVIDER: Web3 = None
    NONCE: int = None

    def __init__(self, w3_endpoint: str) -> None:
        self.endpoint = w3_endpoint
        self.w3 = get_web3_provider(w3_endpoint)

    def set_web3_provider(endpoint: str):
        Contract.W3_PROVIDER = get_web3_provider(endpoint)

        if Contract.PRIVATE_KEY is not None:
            Contract.W3_PROVIDER.eth.default_account = Contract.W3_PROVIDER.eth.account.from_key(
                Contract.PRIVATE_KEY)

    @staticmethod
    def send_contract_call(call, value: float = None):

        if Contract.PRIVATE_KEY is not None:

            txn = call.buildTransaction() if value is None else call.buildTransaction(
                {"value": to_wei(value, "ether")}
            )

            account_address = Contract.W3_PROVIDER.eth.account.from_key(
                Contract.PRIVATE_KEY).address

            if Contract.NONCE is None:
                Contract.NONCE = Contract.W3_PROVIDER.eth.get_transaction_count(
                    account_address)
            else:
                Contract.NONCE += 1

            txn["nonce"] = Contract.NONCE

            signed_txn = Contract.W3_PROVIDER.eth.account.sign_transaction(
                txn, Contract.PRIVATE_KEY)
            return Contract.W3_PROVIDER.eth.send_raw_transaction(signed_txn.rawTransaction)
        else:

            return (
                call.transact({"value": to_wei(value, "ether")})
                if value is not None
                else call.transact()
            )

    @staticmethod
    def set_private_key(key: str):
        Contract.PRIVATE_KEY = key

    def get_wallet_address(self, default=None):

        if Contract.PRIVATE_KEY is None:

            return self.w3.eth.accounts[0] if default is None else default

        account = self.w3.eth.account.from_key(Contract.PRIVATE_KEY)
        self.w3.eth.default_account = account.address

        return account.address


class AssetFactory(Contract):

    def __init__(self, http_endpoint: str, factory_address: str, owner_address: str = None) -> None:
        super().__init__(http_endpoint)
        self.owner_address = self.get_wallet_address(default=owner_address)
        self.factory_contract = get_AssetFactory_contract(
            http_endpoint, factory_address, self.get_wallet_address(default=owner_address))

    def deploy_asset_agreement(self, name: str, symbol: str, market_address: str = None) -> str:

        tx_hash = Contract.send_contract_call(self.factory_contract.functions.createNewAssetAgreement(name, symbol,
                                                                                                      market_address))
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=600
        )

        # web3.py v5 uses camelCase `processReceipt`
        data = self.factory_contract.events.NewContract().processReceipt(
            tx_receipt
        )

        # contract_address = data[0]["args"]["contractAddress"]
        if data and len(data) > 0:
            contract_address = data[0]["args"]["contractAddress"]
        else:
            raise ValueError("No logs found. Contract may not have deployed correctly.")


        return contract_address, tx_receipt.gasUsed

    @staticmethod
    @ContractDeployOnce("factory")
    def deploy(http_endpoint: str, owner_address: str, market_address: str):
        w3 = Web3(Web3.HTTPProvider(http_endpoint))
        w3.eth.default_account = owner_address

        w3_contract = w3.eth.contract(
            abi=get_factory_abi(), bytecode=get_factory_bytecode())

        tx_hash = Contract.send_contract_call(
            w3_contract.constructor(market_address))

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

        return tx_receipt.contractAddress, tx_receipt.gasUsed


class AssetMarket(Contract):

    def __init__(self, http_endpoint: str, market_address: str, buyer_address: str = None) -> None:
        super().__init__(http_endpoint)
        self.address = market_address
        self.buyer = self.get_wallet_address(default=buyer_address)
        self.market_contract = get_Market_contract(
            http_endpoint, market_address, self.buyer)

    @staticmethod
    @ContractDeployOnce("market")
    def deploy(http_endpoint: str, wallet_address: str = None):
        w3 = get_web3_provider(http_endpoint)
        w3.eth.default_account = wallet_address

        w3_contract = w3.eth.contract(
            abi=get_market_abi(), bytecode=get_market_bytecode())

        tx_hash = Contract.send_contract_call(w3_contract.constructor())

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

        return tx_receipt.contractAddress, tx_receipt.gasUsed

    def get_asset_sale_record(self, agreement_address: str, hash: bytes):
        return self.market_contract.functions.getAssetSaleRecord(agreement_address, hash).call()

    def update_hash(self, agreement_address: str, tokenID: int, hash: bytes):
        tx_hash = Contract.send_contract_call(self.market_contract.functions.updateHash(
            agreement_address, tokenID, hash))
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def update_market_royalty(self, royalty: float):

        v = to_wei(royalty, "ether")

        tx_hash = Contract.send_contract_call(self.market_contract.functions.updateMarketRoyalty(
            v))
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def withdraw_royalty(self, address: str):

        tx_hash = Contract.send_contract_call(self.market_contract.functions.withdrawRoyalty(
            address))

        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def update_sale_status(self, agreement: str, tokenID: int, status: bool):
        tx_hash = Contract.send_contract_call(self.market_contract.functions.updateSaleStatus(
            agreement,  tokenID, status))

        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
        
        # Kiểm tra transaction status
        if tx_receipt.status != 1:
            raise Exception(f"Transaction failed with status: {tx_receipt.status}. Transaction hash: {tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash}")
        
        return tx_receipt

    def update_price(self, agreement: str, tokenID: int, price: float):
        v = to_wei(price, "ether")
        tx_hash = Contract.send_contract_call(self.market_contract.functions.updatePrice(
            agreement, tokenID, v))
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def purchase(self, agreement_address: str, tokenID: int, price: float):
        tx_hash = Contract.send_contract_call(self.market_contract.functions.purchase(
            agreement_address, tokenID), price)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)


class AssetAgreement(Contract):

    def __init__(self, http_endpoint: str, agreement_address: str, owner_address: str = None) -> None:
        super().__init__(http_endpoint)
        self.agreement_contract = get_Agreement_contract(
            http_endpoint, agreement_address, self.get_wallet_address(default=owner_address))

    def owner_of(self, tokenID: int):
        return self.agreement_contract.functions.ownerOf(tokenID).call()

    def get_next_token_id(self):
        # AssetAgreement.sol (ERC721A) does not expose getNextTokenId(),
        # but it does expose totalSupply(). Since token IDs are sequential
        # starting from 0 and there is no burn in this demo, the next token
        # ID equals the current totalSupply.
        return self.agreement_contract.functions.totalSupply().call()

    def fetch_asset_metadata(self, tokenID: int):
        """
        Compatibility helper used by the original demo UI.
        The Solidity contract does NOT expose a single fetchAssetMetaData()
        function; instead we compose the metadata from individual getters:
        - priceOf(_tokenId)
        - isForSale(_tokenId)
        - isResaleAllowed(_tokenId)

        Return format keeps backward-compatibility with the original Python:
        (price_wei, assetHash_placeholder, forSale, resaleAllowed)
        """
        price_wei = self.agreement_contract.functions.priceOf(tokenID).call()
        for_sale = self.agreement_contract.functions.isForSale(tokenID).call()
        resale_allowed = self.agreement_contract.functions.isResaleAllowed(tokenID).call()
        # assetHash is not readable on-chain in current Solidity, so we return None
        return price_wei, None, for_sale, resale_allowed

    def get_owner(self):
        return self.agreement_contract.functions.getOwner().call()

    def get_owner_royalty(self):
        return self.agreement_contract.functions.getOwnerRoyalty().call()

    def update_owner_royalty(self, royalty: float):

        v = to_wei(royalty, "ether")

        tx_hash = Contract.send_contract_call(self.agreement_contract.functions.updateOwnerRoyalty(
            v))

        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def get_market_address(self):

        return self.agreement_contract.functions.getMarketAddress().call()

    def get_owner_of_asset_from_hash(self, hash: bytes):
        address = self.agreement_contract.functions.getOwnerOfAssetFromHash(
            hash).call()
        return address

    def price_of(self, tokenID: int):
        value = self.agreement_contract.functions.priceOf(tokenID).call()
        value_eth = from_wei(value, "ether")
        return float(value_eth)

    def update_market_address(self, address: str):

        tx_hash = Contract.send_contract_call(self.agreement_contract.functions.updateMarketAddress(
            address))
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def is_for_sale(self, tokenID: int):

        return self.agreement_contract.functions.isForSale(tokenID).call()

    def is_resale_allowed(self, tokenID: int):

        return self.agreement_contract.functions.isResaleAllowed(tokenID).call()

    def update_sale_status(self, tokenID: int, status: bool):

        tx_hash = Contract.send_contract_call(self.agreement_contract.functions.updateSaleStatus(
            tokenID, status))

        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def update_allow_resale_status(self, tokenID: int, status: bool):
        tx_hash = Contract.send_contract_call(self.agreement_contract.functions.updateAllowResaleStatus(
            tokenID, status))

        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def mint(self, prices: 'list[float]', resaleAllowed: 'list[bool]'):
        v = [to_wei(r, "ether") for r in prices]
        tx_hash = Contract.send_contract_call(self.agreement_contract.functions.mint(
            v, resaleAllowed))

        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def set_approval_for_all(self, operator: str, approved: bool):
        tx_hash = Contract.send_contract_call(self.agreement_contract.functions.setApprovalForAll(
            operator, approved))
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

    def token_uri(self, tokenID: int):

        uri = self.agreement_contract.functions.tokenURI(tokenID).call()

        return uri
