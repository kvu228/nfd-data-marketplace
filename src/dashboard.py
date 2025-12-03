import streamlit as st
from upload import Upload
from contract import AssetAgreement, AssetMarket
from PIL import Image
from constants import LOCAL_ENDPOINT
from web3 import Web3
from db import get_demo_db


class Dashboard:

    def __init__(self, market_address: str) -> None:
        self.market_address = market_address

    def render(self):
        st.write("## Dashboard")
        st.write("View Purchased Assets")

        con = get_demo_db()
        res = con.execute("SELECT uname FROM users")
        user = st.selectbox("User", map(lambda r: r[0], res.fetchall()))

        res = con.execute(
            "SELECT users.wallet FROM users WHERE users.uname = ?", [user])

        if (d := res.fetchone()) is None:
            con.close()
            return

        selected_user_wallet, = d

        res = con.execute(
            "SELECT users.uname, users.agreement, assets.filepath, assets.token_id FROM users LEFT JOIN assets ON users.id = assets.owner_id")
        images = res.fetchall()

        for i, (user_name, user_agreement, asset_filepath, asset_token_id) in enumerate(images):

            if user_agreement is None:
                continue

            agreement = AssetAgreement(
                LOCAL_ENDPOINT, user_agreement, selected_user_wallet)

            price, assetHash, forSale, resaleAllowed = agreement.fetch_asset_metadata(
                asset_token_id)

            if selected_user_wallet != agreement.owner_of(asset_token_id):
                continue

            # Kiểm tra lại resaleAllowed từ contract để đảm bảo giá trị chính xác
            try:
                resaleAllowed_check = agreement.is_resale_allowed(asset_token_id)
                if resaleAllowed != resaleAllowed_check:
                    resaleAllowed = resaleAllowed_check
            except:
                pass

            pil_img = Image.open(asset_filepath)

            pil_img = pil_img.resize((pil_img.width//4, pil_img.height//4))

            st.image(pil_img, "Original Owner: %s. Price (%f ETH). Resale: %r. For Sale: %r" % (
                user_name, Web3.fromWei(price, "ether"), resaleAllowed, forSale))

            # Hiển thị thông báo nếu resale không được phép
            if not resaleAllowed:
                st.warning("⚠️ Resale is not allowed for this asset. It was set when the asset was first minted.")

            sale_status = st.button(
                "Toggle Sale Status", disabled=not resaleAllowed, key=i)

            if sale_status:

                new_sale_status = not forSale
                
                # Kiểm tra lại resaleAllowed trước khi update
                try:
                    resaleAllowed_final = agreement.is_resale_allowed(asset_token_id)
                    if new_sale_status and not resaleAllowed_final:
                        st.error("❌ Cannot enable sale: Resale is not allowed for this asset.")
                        con.close()
                        return
                except Exception as e:
                    st.error(f"❌ Error checking resale status: {str(e)}")
                    con.close()
                    return
                
                market = AssetMarket(
                    LOCAL_ENDPOINT, self.market_address, selected_user_wallet)

                try:
                    # Kiểm tra lại giá trị hiện tại trước khi update
                    current_forSale = agreement.is_for_sale(asset_token_id)
                    current_resaleAllowed = agreement.is_resale_allowed(asset_token_id)
                    
                    st.info(f"📊 Current status: forSale={current_forSale}, resaleAllowed={current_resaleAllowed}")
                    st.info(f"🔄 Attempting to set forSale to: {new_sale_status}")
                    
                    # Update sale status
                    tx_receipt = market.update_sale_status(
                        user_agreement, asset_token_id, new_sale_status)
                    
                    # Kiểm tra transaction status
                    if tx_receipt.status != 1:
                        st.error(f"❌ Transaction failed with status: {tx_receipt.status}")
                        st.error(f"Transaction hash: {tx_receipt.transactionHash.hex() if hasattr(tx_receipt.transactionHash, 'hex') else tx_receipt.transactionHash}")
                    else:
                        # Verify lại giá trị sau khi update
                        agreement_refresh = AssetAgreement(
                            LOCAL_ENDPOINT, user_agreement, selected_user_wallet)
                        updated_forSale = agreement_refresh.is_for_sale(asset_token_id)
                        
                        if updated_forSale == new_sale_status:
                            st.success(f"✅ Successfully updated For Sale status to {new_sale_status}")
                        else:
                            st.warning(f"⚠️ Update may have failed. Expected: {new_sale_status}, Got: {updated_forSale}")
                        
                        # Set approval for market
                        agreement_refresh.set_approval_for_all(self.market_address, True)

                    with st.expander("Log"):
                        st.write("Updated For Sale status of Token %d to %r" %
                                 (asset_token_id, new_sale_status))
                        st.write(f"Transaction hash: {tx_receipt.transactionHash.hex() if hasattr(tx_receipt.transactionHash, 'hex') else tx_receipt.transactionHash}")
                        st.write(f"Transaction status: {'✅ Success' if tx_receipt.status == 1 else '❌ Failed'}")
                except Exception as e:
                    st.error(f"❌ Failed to update sale status: {str(e)}")
                    st.info("💡 This might happen if:")
                    st.info("   - Resale is not allowed for this asset")
                    st.info("   - You don't have permission to update sale status")
                    st.info("   - Transaction was reverted by smart contract")

        con.close()
