# core polymarket api
# https://github.com/Polymarket/py-clob-client/tree/main/examples

import os
import pdb
import time
import ast
import requests

from dotenv import load_dotenv

from web3 import Web3
from web3.constants import MAX_INT

try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # web3 v7+ moved this to a different location
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware

import httpx
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.constants import AMOY, POLYGON
from py_order_utils.builders import OrderBuilder
from py_order_utils.model import OrderData
from py_order_utils.signer import Signer
from py_clob_client.clob_types import (
    OrderArgs,
    MarketOrderArgs,
    OrderType,
    OrderBookSummary,
)
from py_clob_client.order_builder.constants import BUY

from agents.utils.objects import SimpleMarket, SimpleEvent

load_dotenv()


class Polymarket:
    def __init__(self) -> None:
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.gamma_markets_endpoint = self.gamma_url + "/markets"
        self.gamma_events_endpoint = self.gamma_url + "/events"

        self.clob_url = "https://clob.polymarket.com"
        self.clob_auth_endpoint = self.clob_url + "/auth/api-key"

        self.chain_id = 137  # POLYGON
        self.private_key = os.getenv("POLYGON_WALLET_PRIVATE_KEY")
        self.polygon_rpc = "https://polygon-rpc.com"
        self.w3 = Web3(Web3.HTTPProvider(self.polygon_rpc))

        self.exchange_address = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"
        self.neg_risk_exchange_address = "0xC5d563A36AE78145C45a50134d48A1215220f80a"

        self.erc20_approve = """[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"authorizer","type":"address"},{"indexed":true,"internalType":"bytes32","name":"nonce","type":"bytes32"}],"name":"AuthorizationCanceled","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"authorizer","type":"address"},{"indexed":true,"internalType":"bytes32","name":"nonce","type":"bytes32"}],"name":"AuthorizationUsed","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"account","type":"address"}],"name":"Blacklisted","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"userAddress","type":"address"},{"indexed":false,"internalType":"address payable","name":"relayerAddress","type":"address"},{"indexed":false,"internalType":"bytes","name":"functionSignature","type":"bytes"}],"name":"MetaTransactionExecuted","type":"event"},{"anonymous":false,"inputs":[],"name":"Pause","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"newRescuer","type":"address"}],"name":"RescuerChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"previousAdminRole","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"newAdminRole","type":"bytes32"}],"name":"RoleAdminChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":true,"internalType":"address","name":"account","type":"address"},{"indexed":true,"internalType":"address","name":"sender","type":"address"}],"name":"RoleGranted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":true,"internalType":"address","name":"account","type":"address"},{"indexed":true,"internalType":"address","name":"sender","type":"address"}],"name":"RoleRevoked","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"account","type":"address"}],"name":"UnBlacklisted","type":"event"},{"anonymous":false,"inputs":[],"name":"Unpause","type":"event"},{"inputs":[],"name":"APPROVE_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"BLACKLISTER_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"CANCEL_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DECREASE_ALLOWANCE_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DEFAULT_ADMIN_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DEPOSITOR_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"EIP712_VERSION","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"INCREASE_ALLOWANCE_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"META_TRANSACTION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PAUSER_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RESCUER_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"TRANSFER_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"WITHDRAW_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"approveWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"authorizer","type":"address"},{"internalType":"bytes32","name":"nonce","type":"bytes32"}],"name":"authorizationState","outputs":[{"internalType":"enum GasAbstraction.AuthorizationState","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"blacklist","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"blacklisters","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"authorizer","type":"address"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"cancelAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"decrement","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"decreaseAllowanceWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"bytes","name":"depositData","type":"bytes"}],"name":"deposit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"userAddress","type":"address"},{"internalType":"bytes","name":"functionSignature","type":"bytes"},{"internalType":"bytes32","name":"sigR","type":"bytes32"},{"internalType":"bytes32","name":"sigS","type":"bytes32"},{"internalType":"uint8","name":"sigV","type":"uint8"}],"name":"executeMetaTransaction","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"}],"name":"getRoleAdmin","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"getRoleMember","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"}],"name":"getRoleMemberCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"grantRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"hasRole","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"increment","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"increaseAllowanceWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"newName","type":"string"},{"internalType":"string","name":"newSymbol","type":"string"},{"internalType":"uint8","name":"newDecimals","type":"uint8"},{"internalType":"address","name":"childChainManager","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"initialized","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"isBlacklisted","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pausers","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"renounceRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"tokenContract","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueERC20","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"rescuers","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"revokeRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"transferWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"unBlacklist","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"newName","type":"string"},{"internalType":"string","name":"newSymbol","type":"string"}],"name":"updateMetadata","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"withdrawWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"}]"""
        self.erc1155_set_approval = """[{"inputs": [{ "internalType": "address", "name": "operator", "type": "address" },{ "internalType": "bool", "name": "approved", "type": "bool" }],"name": "setApprovalForAll","outputs": [],"stateMutability": "nonpayable","type": "function"}]"""

        self.usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        self.ctf_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"

        self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.usdc = self.web3.eth.contract(
            address=self.usdc_address, abi=self.erc20_approve
        )
        self.ctf = self.web3.eth.contract(
            address=self.ctf_address, abi=self.erc1155_set_approval
        )

        self._init_api_keys()
        self._init_approvals(False)

    def _init_api_keys(self) -> None:
        self.client = ClobClient(
            self.clob_url, key=self.private_key, chain_id=self.chain_id
        )
        self.credentials = self.client.create_or_derive_api_creds()
        self.client.set_api_creds(self.credentials)
        # print(self.credentials)

    def _init_approvals(self, run: bool = False) -> None:
        if not run:
            return

        priv_key = self.private_key
        pub_key = self.get_address_for_private_key()
        chain_id = self.chain_id
        web3 = self.web3
        nonce = web3.eth.get_transaction_count(pub_key)
        usdc = self.usdc
        ctf = self.ctf

        # CTF Exchange
        raw_usdc_approve_txn = usdc.functions.approve(
            "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E", int(MAX_INT, 0)
        ).build_transaction({"chainId": chain_id, "from": pub_key, "nonce": nonce})
        signed_usdc_approve_tx = web3.eth.account.sign_transaction(
            raw_usdc_approve_txn, private_key=priv_key
        )
        send_usdc_approve_tx = web3.eth.send_raw_transaction(
            signed_usdc_approve_tx.raw_transaction
        )
        usdc_approve_tx_receipt = web3.eth.wait_for_transaction_receipt(
            send_usdc_approve_tx, 600
        )
        print(usdc_approve_tx_receipt)

        nonce = web3.eth.get_transaction_count(pub_key)

        raw_ctf_approval_txn = ctf.functions.setApprovalForAll(
            "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E", True
        ).build_transaction({"chainId": chain_id, "from": pub_key, "nonce": nonce})
        signed_ctf_approval_tx = web3.eth.account.sign_transaction(
            raw_ctf_approval_txn, private_key=priv_key
        )
        send_ctf_approval_tx = web3.eth.send_raw_transaction(
            signed_ctf_approval_tx.raw_transaction
        )
        ctf_approval_tx_receipt = web3.eth.wait_for_transaction_receipt(
            send_ctf_approval_tx, 600
        )
        print(ctf_approval_tx_receipt)

        nonce = web3.eth.get_transaction_count(pub_key)

        # Neg Risk CTF Exchange
        raw_usdc_approve_txn = usdc.functions.approve(
            "0xC5d563A36AE78145C45a50134d48A1215220f80a", int(MAX_INT, 0)
        ).build_transaction({"chainId": chain_id, "from": pub_key, "nonce": nonce})
        signed_usdc_approve_tx = web3.eth.account.sign_transaction(
            raw_usdc_approve_txn, private_key=priv_key
        )
        send_usdc_approve_tx = web3.eth.send_raw_transaction(
            signed_usdc_approve_tx.raw_transaction
        )
        usdc_approve_tx_receipt = web3.eth.wait_for_transaction_receipt(
            send_usdc_approve_tx, 600
        )
        print(usdc_approve_tx_receipt)

        nonce = web3.eth.get_transaction_count(pub_key)

        raw_ctf_approval_txn = ctf.functions.setApprovalForAll(
            "0xC5d563A36AE78145C45a50134d48A1215220f80a", True
        ).build_transaction({"chainId": chain_id, "from": pub_key, "nonce": nonce})
        signed_ctf_approval_tx = web3.eth.account.sign_transaction(
            raw_ctf_approval_txn, private_key=priv_key
        )
        send_ctf_approval_tx = web3.eth.send_raw_transaction(
            signed_ctf_approval_tx.raw_transaction
        )
        ctf_approval_tx_receipt = web3.eth.wait_for_transaction_receipt(
            send_ctf_approval_tx, 600
        )
        print(ctf_approval_tx_receipt)

        nonce = web3.eth.get_transaction_count(pub_key)

        # Neg Risk Adapter
        raw_usdc_approve_txn = usdc.functions.approve(
            "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296", int(MAX_INT, 0)
        ).build_transaction({"chainId": chain_id, "from": pub_key, "nonce": nonce})
        signed_usdc_approve_tx = web3.eth.account.sign_transaction(
            raw_usdc_approve_txn, private_key=priv_key
        )
        send_usdc_approve_tx = web3.eth.send_raw_transaction(
            signed_usdc_approve_tx.raw_transaction
        )
        usdc_approve_tx_receipt = web3.eth.wait_for_transaction_receipt(
            send_usdc_approve_tx, 600
        )
        print(usdc_approve_tx_receipt)

        nonce = web3.eth.get_transaction_count(pub_key)

        raw_ctf_approval_txn = ctf.functions.setApprovalForAll(
            "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296", True
        ).build_transaction({"chainId": chain_id, "from": pub_key, "nonce": nonce})
        signed_ctf_approval_tx = web3.eth.account.sign_transaction(
            raw_ctf_approval_txn, private_key=priv_key
        )
        send_ctf_approval_tx = web3.eth.send_raw_transaction(
            signed_ctf_approval_tx.raw_transaction
        )
        ctf_approval_tx_receipt = web3.eth.wait_for_transaction_receipt(
            send_ctf_approval_tx, 600
        )
        print(ctf_approval_tx_receipt)

    def get_all_markets(self) -> "list[SimpleMarket]":
        markets = []
        res = httpx.get(self.gamma_markets_endpoint)
        if res.status_code == 200:
            for market in res.json():
                try:
                    market_data = self.map_api_to_market(market)
                    markets.append(SimpleMarket(**market_data))
                except Exception as e:
                    print(e)
                    pass
        return markets

    def filter_markets_for_trading(self, markets: "list[SimpleMarket]"):
        tradeable_markets = []
        for market in markets:
            if market.active:
                tradeable_markets.append(market)
        return tradeable_markets

    def get_market(self, token_id: str) -> SimpleMarket:
        params = {"clob_token_ids": token_id}
        res = httpx.get(self.gamma_markets_endpoint, params=params)
        if res.status_code == 200:
            data = res.json()
            market = data[0]
            return self.map_api_to_market(market, token_id)

    def map_api_to_market(self, market, token_id: str = "") -> SimpleMarket:
        market = {
            "id": int(market["id"]),
            "question": market["question"],
            "end": market["endDate"],
            "description": market["description"],
            "active": market["active"],
            # "deployed": market["deployed"],
            "funded": market["funded"],
            "rewardsMinSize": float(market["rewardsMinSize"]),
            "rewardsMaxSpread": float(market["rewardsMaxSpread"]),
            # "volume": float(market["volume"]),
            "spread": float(market["spread"]),
            "outcomes": str(market["outcomes"]),
            "outcome_prices": str(market["outcomePrices"]),
            "clob_token_ids": str(market["clobTokenIds"]),
        }
        if token_id:
            market["clob_token_ids"] = token_id
        return market

    def get_all_events(self) -> "list[SimpleEvent]":
        events = []
        res = httpx.get(self.gamma_events_endpoint)
        if res.status_code == 200:
            print(len(res.json()))
            for event in res.json():
                try:
                    print(1)
                    event_data = self.map_api_to_event(event)
                    events.append(SimpleEvent(**event_data))
                except Exception as e:
                    print(e)
                    pass
        return events

    def map_api_to_event(self, event) -> SimpleEvent:
        description = event["description"] if "description" in event.keys() else ""
        return {
            "id": int(event["id"]),
            "ticker": event["ticker"],
            "slug": event["slug"],
            "title": event["title"],
            "description": description,
            "active": event["active"],
            "closed": event["closed"],
            "archived": event["archived"],
            "new": event["new"],
            "featured": event["featured"],
            "restricted": event["restricted"],
            "end": event["endDate"],
            "markets": ",".join([x["id"] for x in event["markets"]]),
        }

    def filter_events_for_trading(
        self, events: "list[SimpleEvent]"
    ) -> "list[SimpleEvent]":
        tradeable_events = []
        for event in events:
            if (
                event.active
                and not event.restricted
                and not event.archived
                and not event.closed
            ):
                tradeable_events.append(event)
        return tradeable_events

    def get_all_tradeable_events(self) -> "list[SimpleEvent]":
        all_events = self.get_all_events()
        return self.filter_events_for_trading(all_events)

    def get_sampling_simplified_markets(self) -> "list[SimpleEvent]":
        markets = []
        raw_sampling_simplified_markets = self.client.get_sampling_simplified_markets()
        for raw_market in raw_sampling_simplified_markets["data"]:
            token_one_id = raw_market["tokens"][0]["token_id"]
            market = self.get_market(token_one_id)
            markets.append(market)
        return markets

    def get_orderbook(self, token_id: str) -> OrderBookSummary:
        return self.client.get_order_book(token_id)

    def get_orderbook_price(self, token_id: str) -> float:
        return float(self.client.get_price(token_id))

    def get_address_for_private_key(self):
        account = self.w3.eth.account.from_key(str(self.private_key))
        return account.address

    def build_order(
        self,
        market_token: str,
        amount: float,
        nonce: str = str(round(time.time())),  # for cancellations
        side: str = "BUY",
        expiration: str = "0",  # timestamp after which order expires
    ):
        signer = Signer(self.private_key)
        builder = OrderBuilder(self.exchange_address, self.chain_id, signer)

        buy = side == "BUY"
        side = 0 if buy else 1
        maker_amount = amount if buy else 0
        taker_amount = amount if not buy else 0
        order_data = OrderData(
            maker=self.get_address_for_private_key(),
            tokenId=market_token,
            makerAmount=maker_amount,
            takerAmount=taker_amount,
            feeRateBps="1",
            nonce=nonce,
            side=side,
            expiration=expiration,
        )
        order = builder.build_signed_order(order_data)
        return order

    def execute_order(self, price, size, side, token_id) -> str:
        return self.client.create_and_post_order(
            OrderArgs(price=price, size=size, side=side, token_id=token_id)
        )

    def execute_market_order(self, market, amount) -> str:
        token_id = ast.literal_eval(market[0].dict()["metadata"]["clob_token_ids"])[1]
        order_args = MarketOrderArgs(
            token_id=token_id,
            amount=amount,
        )
        signed_order = self.client.create_market_order(order_args)
        print("Execute market order... signed_order ", signed_order)
        resp = self.client.post_order(signed_order, orderType=OrderType.FOK)
        print(resp)
        print("Done!")
        return resp

    def get_usdc_balance(self) -> float:
        balance_res = self.usdc.functions.balanceOf(
            self.get_address_for_private_key()
        ).call()
        return float(balance_res / 10e5)

    # ==================== Account Discovery Methods ====================

    def get_market_trades(
        self, market_condition_id: str = None, limit: int = 100
    ) -> list:
        """
        Fetch recent trades for a market to discover active accounts.
        If no market_condition_id is provided, fetches trades across all markets.
        """
        endpoint = f"{self.clob_url}/trades"
        params = {"limit": limit}
        if market_condition_id:
            params["market"] = market_condition_id

        try:
            res = httpx.get(endpoint, params=params)
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            print(f"Error fetching trades: {e}")
            return []

    def get_market_trade_events(
        self, condition_id: str, limit: int = 100
    ) -> list:
        """Fetch trade events for a specific market condition."""
        try:
            return self.client.get_market_trades_events(condition_id)
        except Exception as e:
            print(f"Error fetching trade events: {e}")
            return []

    def extract_addresses_from_trades(self, trades: list) -> set:
        """Extract unique trader addresses from a list of trades."""
        addresses = set()
        for trade in trades:
            if isinstance(trade, dict):
                if "maker_address" in trade and trade["maker_address"]:
                    addresses.add(trade["maker_address"].lower())
                if "owner" in trade and trade["owner"]:
                    addresses.add(trade["owner"].lower())
                if "taker" in trade and trade["taker"]:
                    addresses.add(trade["taker"].lower())
        return addresses

    def scan_active_accounts(
        self, market_ids: list = None, limit_per_market: int = 100
    ) -> set:
        """
        Scan for active accounts across specified markets.
        If no market_ids provided, scans sampling markets.
        Returns a set of unique addresses.
        """
        all_addresses = set()

        if not market_ids:
            # Get active markets to scan
            try:
                sampling_markets = self.client.get_sampling_simplified_markets()
                market_ids = [
                    m["condition_id"] for m in sampling_markets.get("data", [])
                ]
            except Exception as e:
                print(f"Error getting sampling markets: {e}")
                market_ids = []

        for market_id in market_ids:
            trades = self.get_market_trades(market_id, limit=limit_per_market)
            addresses = self.extract_addresses_from_trades(trades)
            all_addresses.update(addresses)
            print(f"Found {len(addresses)} addresses in market {market_id[:16]}...")

        return all_addresses

    def discover_new_accounts(
        self, known_addresses: set = None, market_ids: list = None
    ) -> dict:
        """
        Discover new accounts by comparing against known addresses.
        Returns dict with 'new' and 'all' address sets.
        """
        if known_addresses is None:
            known_addresses = set()

        current_addresses = self.scan_active_accounts(market_ids)
        new_addresses = current_addresses - known_addresses

        return {
            "new": new_addresses,
            "all": current_addresses,
            "new_count": len(new_addresses),
            "total_count": len(current_addresses),
        }

    def get_account_activity(self, address: str) -> dict:
        """
        Get trading activity for a specific account address.
        Returns trade history and summary stats.
        """
        endpoint = f"{self.clob_url}/trades"
        params = {"maker_address": address, "limit": 100}

        try:
            res = httpx.get(endpoint, params=params)
            if res.status_code == 200:
                trades = res.json()
                return {
                    "address": address,
                    "trade_count": len(trades),
                    "trades": trades,
                    "markets_traded": list(
                        set(t.get("market", "") for t in trades if t.get("market"))
                    ),
                }
            return {"address": address, "trade_count": 0, "trades": [], "markets_traded": []}
        except Exception as e:
            print(f"Error fetching account activity: {e}")
            return {"address": address, "error": str(e)}

    def continuous_account_scanner(
        self,
        known_addresses_file: str = None,
        scan_interval_seconds: int = 60,
        callback=None,
    ):
        """
        Continuously scan for new accounts at specified intervals.
        Optionally save/load known addresses from file.
        Call callback function when new accounts are found.
        """
        import json

        known_addresses = set()

        # Load existing known addresses
        if known_addresses_file:
            try:
                with open(known_addresses_file, "r") as f:
                    known_addresses = set(json.load(f))
                print(f"Loaded {len(known_addresses)} known addresses")
            except FileNotFoundError:
                print("No existing addresses file, starting fresh")

        print(f"Starting continuous account scanner (interval: {scan_interval_seconds}s)")

        while True:
            try:
                result = self.discover_new_accounts(known_addresses)

                if result["new"]:
                    print(f"\n🆕 Found {result['new_count']} new accounts!")
                    for addr in result["new"]:
                        print(f"  - {addr}")

                    # Update known addresses
                    known_addresses.update(result["new"])

                    # Save to file
                    if known_addresses_file:
                        with open(known_addresses_file, "w") as f:
                            json.dump(list(known_addresses), f)

                    # Call callback if provided
                    if callback:
                        callback(result["new"])
                else:
                    print(f"No new accounts found. Total tracked: {len(known_addresses)}")

                time.sleep(scan_interval_seconds)

            except KeyboardInterrupt:
                print("\nScanner stopped by user")
                break
            except Exception as e:
                print(f"Scanner error: {e}")
                time.sleep(scan_interval_seconds)


def test():
    host = "https://clob.polymarket.com"
    key = os.getenv("POLYGON_WALLET_PRIVATE_KEY")
    print(key)
    chain_id = POLYGON

    # Create CLOB client and get/set API credentials
    client = ClobClient(host, key=key, chain_id=chain_id)
    client.set_api_creds(client.create_or_derive_api_creds())

    creds = ApiCreds(
        api_key=os.getenv("CLOB_API_KEY"),
        api_secret=os.getenv("CLOB_SECRET"),
        api_passphrase=os.getenv("CLOB_PASS_PHRASE"),
    )
    chain_id = AMOY
    client = ClobClient(host, key=key, chain_id=chain_id, creds=creds)

    print(client.get_markets())
    print(client.get_simplified_markets())
    print(client.get_sampling_markets())
    print(client.get_sampling_simplified_markets())
    print(client.get_market("condition_id"))

    print("Done!")


class PolymarketAccountScanner:
    """
    Account scanner that tracks Polymarket users via Blockscout API.
    No API key required - uses free Polygon Blockscout explorer.
    """

    def __init__(self):
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.blockscout_api = "https://polygon.blockscout.com/api/v2"

        # Polymarket contract addresses on Polygon
        self.ctf_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"  # CTF token
        self.exchange_address = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"
        self.neg_risk_exchange = "0xC5d563A36AE78145C45a50134d48A1215220f80a"
        self.neg_risk_adapter = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"

        self.contract_addresses = {
            self.ctf_address.lower(),
            self.exchange_address.lower(),
            self.neg_risk_exchange.lower(),
            self.neg_risk_adapter.lower(),
        }

    def get_contract_transactions(self, contract_address: str, next_page_params: dict = None) -> dict:
        """Get recent transactions to a contract via Blockscout API."""
        url = f"{self.blockscout_api}/addresses/{contract_address}/transactions"
        params = {"filter": "to"}

        # Add pagination params if provided
        if next_page_params:
            for key, value in next_page_params.items():
                params[key] = value

        try:
            res = httpx.get(url, params=params, timeout=30)
            if res.status_code == 200:
                return res.json()
            return {"items": []}
        except Exception as e:
            print(f"Blockscout API error: {e}")
            return {"items": []}

    def get_token_transfers(self, contract_address: str, next_page_params: dict = None) -> dict:
        """Get token transfers via Blockscout API."""
        url = f"{self.blockscout_api}/addresses/{contract_address}/token-transfers"
        params = {}

        if next_page_params:
            for key, value in next_page_params.items():
                params[key] = value

        try:
            res = httpx.get(url, params=params, timeout=30)
            if res.status_code == 200:
                return res.json()
            return {"items": []}
        except Exception as e:
            print(f"Blockscout API error: {e}")
            return {"items": []}

    def extract_addresses_from_transactions(self, transactions: list) -> set:
        """Extract unique user addresses from transaction list."""
        addresses = set()
        zero_addr = "0x" + "0" * 40

        for tx in transactions:
            # Get 'from' address (the sender/user)
            from_data = tx.get("from", {})
            if isinstance(from_data, dict):
                from_addr = from_data.get("hash", "").lower()
            else:
                from_addr = str(from_data).lower()

            # Skip zero address and contracts
            if from_addr and from_addr != zero_addr:
                if from_addr not in self.contract_addresses:
                    addresses.add(from_addr)

        return addresses

    def extract_addresses_from_transfers(self, transfers: list) -> set:
        """Extract unique addresses from token transfer list."""
        addresses = set()
        zero_addr = "0x" + "0" * 40

        for transfer in transfers:
            for field in ["from", "to"]:
                addr_data = transfer.get(field, {})
                if isinstance(addr_data, dict):
                    addr = addr_data.get("hash", "").lower()
                else:
                    addr = str(addr_data).lower()

                if addr and addr != zero_addr and addr not in self.contract_addresses:
                    addresses.add(addr)

        return addresses

    def scan_exchange_users(self, num_pages: int = 5) -> set:
        """Scan users who have interacted with Polymarket exchange contracts."""
        all_addresses = set()

        contracts = [
            ("CTF Exchange", self.exchange_address),
            ("NegRisk Exchange", self.neg_risk_exchange),
        ]

        for name, contract in contracts:
            print(f"  Scanning {name}...")
            next_page_params = None

            for page in range(num_pages):
                data = self.get_contract_transactions(contract, next_page_params)
                items = data.get("items", [])

                if not items:
                    break

                addresses = self.extract_addresses_from_transactions(items)
                prev_count = len(all_addresses)
                all_addresses.update(addresses)
                new_in_page = len(all_addresses) - prev_count

                print(f"    Page {page + 1}: {len(items)} txs, +{new_in_page} new addresses (total: {len(all_addresses)})")

                # Get next page params
                next_page_params = data.get("next_page_params")
                if not next_page_params:
                    break

        return all_addresses

    def scan_ctf_transfers(self, num_pages: int = 5) -> set:
        """Scan addresses involved in CTF token transfers."""
        all_addresses = set()
        next_page_params = None

        print("  Scanning CTF token transfers...")
        for page in range(num_pages):
            data = self.get_token_transfers(self.ctf_address, next_page_params)
            items = data.get("items", [])

            if not items:
                break

            addresses = self.extract_addresses_from_transfers(items)
            prev_count = len(all_addresses)
            all_addresses.update(addresses)
            new_in_page = len(all_addresses) - prev_count

            print(f"    Page {page + 1}: {len(items)} transfers, +{new_in_page} new addresses (total: {len(all_addresses)})")

            next_page_params = data.get("next_page_params")
            if not next_page_params:
                break

        return all_addresses

    def scan_active_accounts(self, method: str = "exchange", num_pages: int = 3) -> set:
        """
        Scan for active Polymarket accounts.

        Methods:
        - 'exchange': Scan exchange contract interactions (faster, most active traders)
        - 'ctf': Scan CTF token transfers (position holders)
        - 'all': Both methods combined
        """
        all_addresses = set()

        if method in ("exchange", "all"):
            print("\n📊 Scanning exchange contracts...")
            exchange_users = self.scan_exchange_users(num_pages=num_pages)
            all_addresses.update(exchange_users)
            print(f"  Total from exchanges: {len(exchange_users)}")

        if method in ("ctf", "all"):
            print("\n🎫 Scanning CTF token transfers...")
            ctf_holders = self.scan_ctf_transfers(num_pages=num_pages)
            all_addresses.update(ctf_holders)
            print(f"  Total from CTF transfers: {len(ctf_holders)}")

        return all_addresses

    def get_account_info(self, address: str) -> dict:
        """Get info about an account from Blockscout."""
        url = f"{self.blockscout_api}/addresses/{address}"
        try:
            res = httpx.get(url, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return {
                    "address": address,
                    "tx_count": data.get("transactions_count", 0),
                    "token_transfers": data.get("token_transfers_count", 0),
                    "is_contract": data.get("is_contract", False),
                    "blockscout_url": f"https://polygon.blockscout.com/address/{address}"
                }
        except Exception as e:
            print(f"Error: {e}")

        return {"address": address, "error": "Could not fetch info"}

    def discover_new_accounts(self, known_addresses: set = None, method: str = "exchange") -> dict:
        """Discover new accounts by comparing against known addresses."""
        if known_addresses is None:
            known_addresses = set()

        current_addresses = self.scan_active_accounts(method=method)
        new_addresses = current_addresses - known_addresses

        return {
            "new": new_addresses,
            "all": current_addresses,
            "new_count": len(new_addresses),
            "total_count": len(current_addresses),
        }

    def continuous_scan(
        self,
        known_addresses_file: str = "known_addresses.json",
        scan_interval_seconds: int = 60,
        callback=None,
    ):
        """Continuously scan for new accounts."""
        import json

        known_addresses = set()

        # Load existing
        try:
            with open(known_addresses_file, "r") as f:
                known_addresses = set(json.load(f))
            print(f"Loaded {len(known_addresses)} known addresses")
        except FileNotFoundError:
            print("Starting with empty address list")

        print(f"Starting continuous scanner (interval: {scan_interval_seconds}s)")
        print("Press Ctrl+C to stop\n")

        while True:
            try:
                result = self.discover_new_accounts(known_addresses, method="exchange")

                if result["new"]:
                    print(f"\n🆕 Found {result['new_count']} new accounts!")
                    for addr in list(result["new"])[:10]:
                        print(f"  - {addr}")
                    if result["new_count"] > 10:
                        print(f"  ... and {result['new_count'] - 10} more")

                    known_addresses.update(result["new"])

                    with open(known_addresses_file, "w") as f:
                        json.dump(list(known_addresses), f)

                    if callback:
                        callback(result["new"])
                else:
                    print(f"No new accounts. Total tracked: {len(known_addresses)}")

                time.sleep(scan_interval_seconds)

            except KeyboardInterrupt:
                print("\nScanner stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(scan_interval_seconds)


def demo_account_scanner():
    """Demo the account scanning functionality."""
    print("=" * 60)
    print("Polymarket Account Scanner Demo")
    print("=" * 60)
    print("Scanning Polymarket activity via Blockscout API...")
    print("(Free, no API key required)\n")

    scanner = PolymarketAccountScanner()

    # Scan for active accounts using CTF transfers (most diverse results)
    print("Scanning for active Polymarket accounts...")
    addresses = scanner.scan_active_accounts(method="ctf", num_pages=5)

    print(f"\n✅ Found {len(addresses)} unique trader addresses:")
    print("-" * 50)
    for i, addr in enumerate(sorted(list(addresses))[:25]):
        print(f"  {i+1:2}. {addr}")
    if len(addresses) > 25:
        print(f"  ... and {len(addresses) - 25} more")

    # Get info on sample account
    if addresses:
        sample = sorted(list(addresses))[0]
        print(f"\n📋 Sample account info:")
        info = scanner.get_account_info(sample)
        print(f"   Address: {sample}")
        print(f"   Total transactions: {info.get('tx_count', 'N/A')}")
        print(f"   Token transfers: {info.get('token_transfers', 'N/A')}")
        print(f"   View: {info.get('blockscout_url', 'N/A')}")

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total unique accounts: {len(addresses)}")
    print(f"  Data source: Blockscout API (Polygon CTF token transfers)")
    print("=" * 60)
    print("\nUsage:")
    print("  scanner = PolymarketAccountScanner()")
    print("  addresses = scanner.scan_active_accounts(method='ctf', num_pages=10)")
    print("  scanner.continuous_scan('known_addresses.json', 60)")
    print("=" * 60)


def gamma():
    url = "https://gamma-com"
    markets_url = url + "/markets"
    res = httpx.get(markets_url)
    code = res.status_code
    if code == 200:
        markets: list[SimpleMarket] = []
        data = res.json()
        for market in data:
            try:
                market_data = {
                    "id": int(market["id"]),
                    "question": market["question"],
                    # "start": market['startDate'],
                    "end": market["endDate"],
                    "description": market["description"],
                    "active": market["active"],
                    "deployed": market["deployed"],
                    "funded": market["funded"],
                    # "orderMinSize": float(market['orderMinSize']) if market['orderMinSize'] else 0,
                    # "orderPriceMinTickSize": float(market['orderPriceMinTickSize']),
                    "rewardsMinSize": float(market["rewardsMinSize"]),
                    "rewardsMaxSpread": float(market["rewardsMaxSpread"]),
                    "volume": float(market["volume"]),
                    "spread": float(market["spread"]),
                    "outcome_a": str(market["outcomes"][0]),
                    "outcome_b": str(market["outcomes"][1]),
                    "outcome_a_price": str(market["outcomePrices"][0]),
                    "outcome_b_price": str(market["outcomePrices"][1]),
                }
                markets.append(SimpleMarket(**market_data))
            except Exception as err:
                print(f"error {err} for market {id}")
        pdb.set_trace()
    else:
        raise Exception()


def main():
    # auth()
    # test()
    # gamma()
    print(Polymarket().get_all_events())


if __name__ == "__main__":
    load_dotenv()
    import sys

    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "scan":
            # Run account scanner demo
            demo_account_scanner()
            sys.exit(0)
        elif sys.argv[1] == "scan-continuous":
            # Run continuous scanner (no auth required)
            scanner = PolymarketAccountScanner()
            output_file = sys.argv[2] if len(sys.argv) > 2 else "known_addresses.json"
            interval = int(sys.argv[3]) if len(sys.argv) > 3 else 60
            scanner.continuous_scan(output_file, interval)
            sys.exit(0)

    p = Polymarket()

    # k = p.get_api_key()
    # m = p.get_sampling_simplified_markets()

    # print(m)
    # m = p.get_market('11015470973684177829729219287262166995141465048508201953575582100565462316088')

    # t = m[0]['token_id']
    # o = p.get_orderbook(t)
    # pdb.set_trace()

    """
    
    (Pdb) pprint(o)
            OrderBookSummary(
                market='0x26ee82bee2493a302d21283cb578f7e2fff2dd15743854f53034d12420863b55', 
                asset_id='11015470973684177829729219287262166995141465048508201953575582100565462316088', 
                bids=[OrderSummary(price='0.01', size='600005'), OrderSummary(price='0.02', size='200000'), ...
                asks=[OrderSummary(price='0.99', size='100000'), OrderSummary(price='0.98', size='200000'), ...
            )
    
    """

    # https://polygon-rpc.com

    test_market_token_id = (
        "101669189743438912873361127612589311253202068943959811456820079057046819967115"
    )
    test_market_data = p.get_market(test_market_token_id)

    # test_size = 0.0001
    test_size = 1
    test_side = BUY
    test_price = float(ast.literal_eval(test_market_data["outcome_prices"])[0])

    # order = p.execute_order(
    #    test_price,
    #    test_size,
    #    test_side,
    #    test_market_token_id,
    # )

    # order = p.execute_market_order(test_price, test_market_token_id)

    balance = p.get_usdc_balance()
