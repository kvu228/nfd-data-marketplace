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

        self.market_contract_address = AssetMarket.deploy(
            eth_endpoint, self.web3.eth.accounts[0])[0]

        self.factory_address = AssetFactory.deploy(
            eth_endpoint, self.web3.eth.accounts[0], self.market_contract_address)[0]

        # self.owner_registration = OwnerRegistration(
        #     self.factory_address, self.market_contract_address)
        # self.buyer_registration = BuyerRegistration()

        self.user_registration = UserRegistration()

        self.upload = Upload(self.factory_address,
                             self.market_contract_address)
        self.market = Market(self.market_contract_address)
        self.dasboard = Dashboard(self.market_contract_address)

    def render_app(self):

        st.write("# NFT-Based Data Marketplace with Digital Watermarking")
        
        # Sidebar for watermarking algorithm selection
        with st.sidebar:
            st.write("## Configuration")
            # Initialize session state if not present
            if "watermark_method" not in st.session_state:
                st.session_state["watermark_method"] = "lsb"
            
            # Use selectbox with key that syncs to session state
            watermark_method = st.selectbox(
                "Watermarking Algorithm",
                options=["lsb", "ssl"],
                index=0 if st.session_state["watermark_method"] == "lsb" else 1,
                key="watermark_method",
                help="Choose between LSB (Least Significant Bit) or SSL watermarking algorithm"
            )
            st.info(f"Current: **{watermark_method.upper()}** watermarking")
        
        user, dashboard, upload, market, extract = st.tabs(
            ["User Registration", "Dashboard", "Publish Asset", "Trade", "Identifiability/Traceability"])

        hide_img_fs = '''
        <style>
        button[title="View fullscreen"]{
            visibility: hidden;}
        </style>
        '''

        st.markdown(hide_img_fs, unsafe_allow_html=True)
        
        # Initialize ExtractWatermark with selected method
        extractwm = ExtractWatermark(
            self.market_contract_address, 
            watermark_method=st.session_state["watermark_method"]
        )

        with user:
            UserRegistration.render()
        with upload:
            self.upload.render()

        with market:
            self.market.render()

        with extract:
            extractwm.render()

        with dashboard:
            self.dasboard.render()

if __name__ == "__main__":
    st.set_page_config(layout="wide")

    app = NFTApp(LOCAL_ETH_ENDPOINT)

    app.render_app()
