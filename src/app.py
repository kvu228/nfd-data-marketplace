"""
NFT Market Demo

Author: David Yue
"""
import streamlit as st
from contract import AssetFactory, AssetMarket
from provider import get_web3_provider

from user_registration import UserRegistration
from extract_watermark import ExtractWatermark
from dashboard import Dashboard
from market import Market
from upload import Upload

LOCAL_ETH_ENDPOINT = "http://127.0.0.1:8545/"


class NFTApp:

    def __init__(self, eth_endpoint: str) -> None:
        self.web3 = get_web3_provider(eth_endpoint)
        
        # Kiểm tra kết nối với Hardhat node
        if not self.web3.isConnected():
            st.error(f"❌ Không thể kết nối với Hardhat node tại {eth_endpoint}")
            st.error("Vui lòng đảm bảo Hardhat node đang chạy bằng lệnh: `npx hardhat node`")
            st.stop()
        
        # Kiểm tra xem có accounts không
        try:
            accounts = self.web3.eth.accounts
            if len(accounts) == 0:
                st.error("❌ Không tìm thấy accounts trong Hardhat node")
                st.error("Vui lòng đảm bảo Hardhat node đã khởi động đúng cách")
                st.stop()
        except Exception as e:
            st.error(f"❌ Lỗi khi kiểm tra accounts: {str(e)}")
            st.error("Vui lòng đảm bảo Hardhat node đang chạy tại http://127.0.0.1:8545/")
            st.stop()

        try:
            self.market_contract_address = AssetMarket.deploy(
                eth_endpoint, self.web3.eth.accounts[0])[0]

            self.factory_address = AssetFactory.deploy(
                eth_endpoint, self.web3.eth.accounts[0], self.market_contract_address)[0]
        except Exception as e:
            st.error(f"❌ Lỗi khi deploy contracts: {str(e)}")
            st.error("Vui lòng kiểm tra:")
            st.error("1. Hardhat node đang chạy")
            st.error("2. Smart contracts đã được compile: `npx hardhat compile`")
            st.error("3. Có đủ accounts và ETH trong Hardhat node")
            st.stop()

        # self.owner_registration = OwnerRegistration(
        #     self.factory_address, self.market_contract_address)
        # self.buyer_registration = BuyerRegistration()

        self.user_registration = UserRegistration()

        self.upload = Upload(self.factory_address,
                             self.market_contract_address)
        self.market = Market(self.market_contract_address)
        self.extractwm = ExtractWatermark(self.market_contract_address)
        self.dasboard = Dashboard(self.market_contract_address)

    def render_app(self):

        st.write("# NFT-Based Data Marketplace with Digital Watermarking")
        user, dashboard, upload, market, extract = st.tabs(
            ["User Registration", "Dashboard", "Publish Asset", "Trade", "Identifiability/Traceability"])

        hide_img_fs = '''
        <style>
        button[title="View fullscreen"]{
            visibility: hidden;}
        </style>
        '''

        st.markdown(hide_img_fs, unsafe_allow_html=True)

        with user:
            UserRegistration.render()
        with upload:
            self.upload.render()

        with market:
            self.market.render()

        with extract:
            self.extractwm.render()

        with dashboard:
            self.dasboard.render()

if __name__ == "__main__":
    st.set_page_config(layout="wide")

    app = NFTApp(LOCAL_ETH_ENDPOINT)

    app.render_app()
