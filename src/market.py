import streamlit as st
from PIL import Image
from contract import AssetMarket, AssetAgreement, get_web3_provider
from constants import LOCAL_ENDPOINT
from extract_watermark import WatermarkWrapper
from tempfile import NamedTemporaryFile
from Crypto.Hash import SHA256
from web3 import Web3
from db import get_demo_db
from user_utils import get_user_display_options, get_user_from_display
import time


class Market:

    def __init__(self, market_address: str) -> None:
        self.market_address = market_address
        self.manager_address = get_web3_provider(
            LOCAL_ENDPOINT).eth.accounts[0]

    def on_image_buy(self, agreement_address: str, token_id: int, buyer_id: int):

        overall_start = time.time()
        con = get_demo_db()
        timing_log = []

        # Step 1: Get agreement and seller info
        start_time = time.time()
        agreement = AssetAgreement(
            LOCAL_ENDPOINT, agreement_address, self.manager_address)

        asset_price = agreement.price_of(token_id)
        seller_address = agreement.owner_of(token_id)

        res = con.execute(
            "SELECT id FROM users WHERE wallet = ?", [seller_address])
        seller_id, = res.fetchone()
        step1_time = time.time() - start_time
        timing_log.append(f"1. Get agreement and seller info: {step1_time:.3f}s")

        # Step 2: Load image and compute hash
        start_time = time.time()
        wm_image = NamedTemporaryFile(
            "wb", suffix=".png", delete=False)

        res = con.execute(
            "SELECT assets.filepath FROM users LEFT JOIN assets ON users.id = assets.owner_id WHERE users.agreement = ? AND assets.token_id = ?", [agreement_address, token_id])

        img_location, = res.fetchone()

        with open(img_location, "rb") as f:
            data = f.read()
            wm_image.write(data)
            cipher = SHA256.new(data)
            cipher.update(bytes([seller_id, buyer_id]))
            img_hash = cipher.digest()
            img_hash_hex = cipher.hexdigest()
        step2_time = time.time() - start_time
        timing_log.append(f"2. Load image and compute hash: {step2_time:.3f}s")

        wm_file_name = wm_image.name
        wm_image.close()

        # Step 3: Watermark the image
        start_time = time.time()
        watermark_method = st.session_state.get("watermark_method", "lsb")
        wm = WatermarkWrapper(watermark_method)

        wm.set_watermark(seller_id, buyer_id)
        wm.watermark_image(wm_file_name)
        step3_time = time.time() - start_time
        timing_log.append(f"3. Watermark image ({watermark_method.upper()}): {step3_time:.3f}s")

        # Step 4: Update hash on smart contract
        start_time = time.time()
        asset_market_manager = AssetMarket(
            LOCAL_ENDPOINT, self.market_address, self.manager_address)

        update_hash_receipt = asset_market_manager.update_hash(
            agreement_address, token_id, img_hash)
        step4_time = time.time() - start_time
        update_hash_gas = update_hash_receipt.gasUsed
        # Get gas price and calculate fee
        update_hash_tx = asset_market_manager.w3.eth.get_transaction(update_hash_receipt.transactionHash)
        update_hash_gas_price = update_hash_tx.get('gasPrice') or update_hash_receipt.get('effectiveGasPrice', 0)
        update_hash_fee_wei = update_hash_gas * update_hash_gas_price
        update_hash_fee_eth = Web3.fromWei(update_hash_fee_wei, 'ether')
        timing_log.append(f"4. Update hash on smart contract: {step4_time:.3f}s (Gas: {update_hash_gas:,} gas, Fee: {update_hash_fee_eth:.9f} ETH)")
        
        # Step 5: Get buyer wallet and transfer asset
        start_time = time.time()
        res = con.execute("SELECT wallet FROM users WHERE id = ?", [buyer_id])
        buyer_wallet_address, = res.fetchone()

        asset_market = AssetMarket(
            LOCAL_ENDPOINT, self.market_address, buyer_wallet_address)
        purchase_receipt = asset_market.purchase(
            agreement_address, token_id, asset_price)
        step5_time = time.time() - start_time
        purchase_gas = purchase_receipt.gasUsed
        # Get gas price and calculate fee
        purchase_tx = asset_market.w3.eth.get_transaction(purchase_receipt.transactionHash)
        purchase_gas_price = purchase_tx.get('gasPrice') or purchase_receipt.get('effectiveGasPrice', 0)
        purchase_fee_wei = purchase_gas * purchase_gas_price
        purchase_fee_eth = Web3.fromWei(purchase_fee_wei, 'ether')
        timing_log.append(f"5. Transfer asset to buyer: {step5_time:.3f}s (Gas: {purchase_gas:,} gas, Fee: {purchase_fee_eth:.9f} ETH)")
        
        # Calculate total gas and total fee
        total_gas = update_hash_gas + purchase_gas
        total_fee_eth = update_hash_fee_eth + purchase_fee_eth

        total_time = time.time() - overall_start
        timing_log.append(f"**Total time: {total_time:.3f}s**")
        timing_log.append(f"**Total gas used: {total_gas:,} gas**")
        timing_log.append(f"**Total gas fee: {total_fee_eth:.9f} ETH**")

        # Display success message with total time prominently
        st.success(f"✅ Purchase completed successfully in {total_time:.3f}s")
        
        # Display summary information
        st.write("**Purchase Summary:**")
        st.write(f"- Watermark text: {seller_id}, {buyer_id}")
        st.write(f"- Image Hash: {img_hash_hex}")
        st.write(f"- Price: {asset_price} ETH, Token ID: {token_id}")
        st.write(f"- Watermarking method: {watermark_method.upper()}")
        st.write(f"- **Total Gas Used: {total_gas:,} gas**")
        st.write(f"- **Total Gas Fee: {total_fee_eth:.9f} ETH**")

        # Detailed timing log in expander
        with st.expander("📊 Detailed Runtime Log"):
            st.write("**Step-by-step timing:**")
            for log_entry in timing_log:
                st.write(log_entry)

        with open(wm_file_name, "rb") as f:
            st.download_button("Verify Signature and Download Asset",
                               f, file_name=wm_file_name)

        con.close()

    def render(self):
        st.write("## Trade")
        st.write(
            "Every owner's published asset appears on this page and buyers can buy whichever one they wish")

        con = get_demo_db()

        display_options, user_data_dict = get_user_display_options(include_balance=True)
        
        if not display_options:
            st.warning("No users registered yet.")
            con.close()
            return

        selected_display = st.selectbox("Buyer", options=display_options)
        buyer = get_user_from_display(selected_display, user_data_dict)
        c1, c2 = st.columns(2)

        res = con.execute("SELECT id FROM users WHERE uname = ?", [buyer])

        if (d := res.fetchone()) is None:
            con.close()
            return

        buyer_id, = d

        res = con.execute(
            "SELECT * FROM users INNER JOIN assets ON users.id = assets.owner_id")

        data = res.fetchall()

        i = 0

        for (_, owner_name, owner_wallet, owner_agreement, _, _, asset_filepath, asset_token_id) in data:

            c = [c1, c2][i % 2]

            agreement = AssetAgreement(
                LOCAL_ENDPOINT, owner_agreement, owner_wallet)

            seller_address = agreement.owner_of(asset_token_id)

            res = con.execute(
                "SELECT uname FROM users WHERE wallet = ?", [seller_address])
            data = res.fetchone()

            seller_name, = data

            price, _, forSale, resaleAllowed = agreement.fetch_asset_metadata(
                asset_token_id)

            if not forSale:
                continue

            pil_img = Image.open(asset_filepath)

            pil_img = pil_img.resize((pil_img.width//4, pil_img.height//4))

            c.image(pil_img, "Original Owner: %s. Seller: %s. Price (%f ETH). Resale: %r" % (
                owner_name, seller_name, Web3.fromWei(price, "ether"), resaleAllowed))

            buy = c.button("Buy", key=asset_filepath)

            i += 1

            if buy:
                self.on_image_buy(owner_agreement, asset_token_id, buyer_id)

        con.close()
