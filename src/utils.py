from json import loads
from provider import get_web3_provider
from Crypto.Util.strxor import strxor
from web3 import Web3


def from_wei(value, unit='ether'):
    """
    Convert wei to ether (compatible with different web3.py versions).
    
    Args:
        value: Value in wei
        unit: Unit to convert to (default: 'ether')
    
    Returns:
        Value in the specified unit
    """
    try:
        # Try web3.py v6+ format (from_wei as class method)
        return Web3.from_wei(value, unit)
    except AttributeError:
        try:
            # Try web3.py v5 format (fromWei as class method)
            return Web3.fromWei(value, unit)
        except AttributeError:
            # Fallback: manual conversion for ether
            if unit == 'ether':
                return value / 1e18
            else:
                raise ValueError(f"Unsupported unit: {unit}")


def to_wei(value, unit='ether'):
    """
    Convert ether to wei (compatible with different web3.py versions).
    
    Args:
        value: Value in ether (or specified unit)
        unit: Unit to convert from (default: 'ether')
    
    Returns:
        Value in wei
    """
    try:
        # Try web3.py v6+ format (to_wei as class method)
        return Web3.to_wei(value, unit)
    except AttributeError:
        try:
            # Try web3.py v5 format (toWei as class method)
            return Web3.toWei(value, unit)
        except AttributeError:
            # Fallback: manual conversion for ether
            if unit == 'ether':
                return int(value * 1e18)
            else:
                raise ValueError(f"Unsupported unit: {unit}")


def xor_cipher(data: bytes, key: bytes):

    xor_key = key * (len(data)//len(key)) + key[:len(data) % len(key)]

    return strxor(data, xor_key)


def get_market_abi():
    market_abi_file = open(
        "artifacts/contracts/AssetMarket.sol/AssetMarket.json", "r")
    market_abi = loads(market_abi_file.read())["abi"]

    return market_abi


def get_market_bytecode():
    market_abi_file = open(
        "artifacts/contracts/AssetMarket.sol/AssetMarket.json", "r")
    market_bytecode = loads(market_abi_file.read())["bytecode"]

    return market_bytecode


def get_factory_bytecode():
    factory_bytecode_file = open(
        "artifacts/contracts/AssetAgreementFactory.sol/AssetAgreementFactory.json", "r")
    factory_bytecode = loads(factory_bytecode_file.read())["bytecode"]

    return factory_bytecode


def get_factory_abi():
    factory_abi_file = open(
        "artifacts/contracts/AssetAgreementFactory.sol/AssetAgreementFactory.json", "r")
    factory_abi = loads(factory_abi_file.read())["abi"]

    return factory_abi


def get_agreement_abi():
    agreement_abi_file = open(
        "artifacts/contracts/AssetAgreement.sol/AssetAgreement.json", "r")
    agreement_abi = loads(agreement_abi_file.read())["abi"]

    return agreement_abi


def get_agreement_bytecode():
    agreement_bytecode_file = open(
        "artifacts/contracts/AssetAgreement.sol/AssetAgreement.json", "r")
    agreement_bytecode = loads(agreement_bytecode_file.read())["bytecode"]

    return agreement_bytecode


def get_Agreement_contract(endpoint: str, address: str, account: str):
    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account
    return w3.eth.contract(address=address, abi=get_agreement_abi())


def get_AssetFactory_contract(endpoint: str, address: str, account: str):
    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account
    return w3.eth.contract(address=address, abi=get_factory_abi())


def get_Market_contract(endpoint: str, address: str, account: str):

    w3 = get_web3_provider(endpoint)
    w3.eth.default_account = account

    return w3.eth.contract(address=address, abi=get_market_abi())
