import streamlit as st
from os.path import basename, join
from uuid import uuid4
from contract import AssetAgreement, AssetFactory
from constants import LOCAL_ENDPOINT
from db import get_demo_db
from web3 import Web3
from user_utils import get_user_display_options, get_user_from_display
import time
from decimal import Decimal


class Upload:

    def __init__(self, factory_address: str, market_address: str) -> None:
        self.market_address = market_address
        self.factory_address = factory_address

    def render(self):
        st.write("## Publish Asset")
        st.write("Owners publish the asset they would like to sell to Marketplace")
        con = get_demo_db()

        with st.form("asset-upload"):
            display_options, user_data_dict = get_user_display_options(include_balance=True)
            
            if not display_options:
                st.warning("No users registered yet. Please register a user first.")
                con.close()
                return

            selected_display = st.selectbox("Owner", options=display_options)
            owner = get_user_from_display(selected_display, user_data_dict)

            asset = st.file_uploader("Asset")
            price = st.number_input("Price (ETH)", min_value=0.0, step=0.01)
            resale = st.checkbox("Resale Allowed")
            submit = st.form_submit_button("Publish")

            if owner is None:
                return

            if not submit or asset is None:
                return

            overall_start = time.time()
            timing_log = []

            # Step 1: Save asset file
            start_time = time.time()
            data = asset.getvalue()
            filename = basename(asset.name)
            ext = filename.split(".")[-1]

            new_file_name = uuid4().hex + "." + ext

            new_file_location = join("images", new_file_name)

            with open(new_file_location, "wb") as f:
                f.write(data)
            step1_time = time.time() - start_time
            timing_log.append(f"1. Save asset file: {step1_time:.3f}s")

            # Step 2: Get owner info
            start_time = time.time()
            res = con.execute(
                "SELECT id, wallet, agreement FROM users WHERE uname = ?", [owner])

            owner_id, owner_wallet, owner_agreement = res.fetchone()
            step2_time = time.time() - start_time
            timing_log.append(f"2. Get owner info: {step2_time:.3f}s")

            # Step 3: Deploy agreement contract (if needed)
            total_gas = 0
            total_fee_eth = Decimal('0.0')
            if owner_agreement is None:
                start_time = time.time()
                factory = AssetFactory(LOCAL_ENDPOINT, self.factory_address, owner_wallet)
                # Call deploy and get receipt to calculate fee
                from contract import Contract
                tx_hash = Contract.send_contract_call(
                    factory.factory_contract.functions.createNewAssetAgreement(
                        "ASSET", "ASSET", self.market_address))
                deploy_receipt = factory.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
                data = factory.factory_contract.events.NewContract().processReceipt(deploy_receipt)
                owner_agreement = data[0]["args"]["contractAddress"]
                deploy_gas = deploy_receipt.gasUsed
                
                agreement = AssetAgreement(
                    LOCAL_ENDPOINT, owner_agreement, owner_wallet)
                approval_receipt = agreement.set_approval_for_all(self.market_address, True)
                approval_gas = approval_receipt.gasUsed
                
                # Calculate fees
                deploy_tx = factory.w3.eth.get_transaction(deploy_receipt.transactionHash)
                deploy_gas_price = deploy_tx.get('gasPrice') or deploy_receipt.get('effectiveGasPrice', 0)
                deploy_fee_eth = Web3.fromWei(deploy_gas * deploy_gas_price, 'ether')
                
                approval_tx = agreement.w3.eth.get_transaction(approval_receipt.transactionHash)
                approval_gas_price = approval_tx.get('gasPrice') or approval_receipt.get('effectiveGasPrice', 0)
                approval_fee_eth = Web3.fromWei(approval_gas * approval_gas_price, 'ether')

                con.execute("UPDATE users SET agreement = ? WHERE id = ?", [
                            owner_agreement, owner_id])
                con.commit()
                step3_time = time.time() - start_time
                step3_gas = deploy_gas + approval_gas
                step3_fee_eth = deploy_fee_eth + approval_fee_eth
                total_gas += step3_gas
                total_fee_eth += step3_fee_eth
                timing_log.append(f"3. Deploy Asset Agreement contract: {step3_time:.3f}s (Gas: {step3_gas:,} gas, Fee: {step3_fee_eth:.9f} ETH)")
            else:
                timing_log.append(f"3. Use existing Asset Agreement contract: 0.000s")

            # Step 4: Mint asset
            start_time = time.time()
            agreement = AssetAgreement(
                LOCAL_ENDPOINT, owner_agreement, owner_wallet)

            token_id = agreement.get_next_token_id()
            mint_receipt = agreement.mint([price], [resale])
            step4_time = time.time() - start_time
            mint_gas = mint_receipt.gasUsed
            # Calculate fee
            mint_tx = agreement.w3.eth.get_transaction(mint_receipt.transactionHash)
            mint_gas_price = mint_tx.get('gasPrice') or mint_receipt.get('effectiveGasPrice', 0)
            mint_fee_eth = Web3.fromWei(mint_gas * mint_gas_price, 'ether')
            total_gas += mint_gas
            total_fee_eth += mint_fee_eth
            timing_log.append(f"4. Mint asset (Token ID: {token_id}): {step4_time:.3f}s (Gas: {mint_gas:,} gas, Fee: {mint_fee_eth:.9f} ETH)")

            # Step 5: Save to database
            start_time = time.time()
            res = con.execute("INSERT INTO assets (owner_id, filepath, token_id) VALUES (?, ?, ?)", [
                              owner_id, new_file_location, token_id])
            con.commit()
            step5_time = time.time() - start_time
            timing_log.append(f"5. Save to database: {step5_time:.3f}s")

            total_time = time.time() - overall_start
            timing_log.append(f"**Total time: {total_time:.3f}s**")
            if total_gas > 0:
                timing_log.append(f"**Total gas used: {total_gas:,} gas**")
                timing_log.append(f"**Total gas fee: {total_fee_eth:.9f} ETH**")

            st.write("Asset %s has been uploaded with Token ID: %d" %
                     (asset.name, token_id))
            st.success(f"✅ Published successfully in {total_time:.3f}s")
            if total_gas > 0:
                st.info(f"⛽ Total Gas Used: {total_gas:,} gas | Total Gas Fee: {total_fee_eth:.9f} ETH")
            
            with st.expander("Publish Log"):
                for log_entry in timing_log:
                    st.write(log_entry)
                st.write(f"Agreement contract: {owner_agreement}")
        con.close()
