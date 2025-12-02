import streamlit as st
from os.path import basename, join
from uuid import uuid4
from contract import AssetAgreement, AssetFactory
from constants import LOCAL_ENDPOINT
from db import get_demo_db
import time


class Upload:

    def __init__(self, factory_address: str, market_address: str) -> None:
        self.market_address = market_address
        self.factory_address = factory_address

    def render(self):
        st.write("## Publish Asset")
        st.write("Owners publish the asset they would like to sell to Marketplace")
        con = get_demo_db()

        with st.form("asset-upload"):

            res = con.execute("SELECT uname FROM users")

            owner = st.selectbox("Owner", options=map(
                lambda r: r[0], res.fetchall()))

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
            if owner_agreement is None:
                start_time = time.time()
                owner_agreement = AssetFactory(LOCAL_ENDPOINT, self.factory_address, owner_wallet).deploy_asset_agreement(
                    "ASSET", "ASSET", self.market_address)[0]
                agreement = AssetAgreement(
                    LOCAL_ENDPOINT, owner_agreement, owner_wallet)
                agreement.set_approval_for_all(self.market_address, True)

                con.execute("UPDATE users SET agreement = ? WHERE id = ?", [
                            owner_agreement, owner_id])
                con.commit()
                step3_time = time.time() - start_time
                timing_log.append(f"3. Deploy Asset Agreement contract: {step3_time:.3f}s")
            else:
                timing_log.append(f"3. Use existing Asset Agreement contract: 0.000s")

            # Step 4: Mint asset
            start_time = time.time()
            agreement = AssetAgreement(
                LOCAL_ENDPOINT, owner_agreement, owner_wallet)

            token_id = agreement.get_next_token_id()
            agreement.mint([price], [resale])
            step4_time = time.time() - start_time
            timing_log.append(f"4. Mint asset (Token ID: {token_id}): {step4_time:.3f}s")

            # Step 5: Save to database
            start_time = time.time()
            res = con.execute("INSERT INTO assets (owner_id, filepath, token_id) VALUES (?, ?, ?)", [
                              owner_id, new_file_location, token_id])
            con.commit()
            step5_time = time.time() - start_time
            timing_log.append(f"5. Save to database: {step5_time:.3f}s")

            total_time = time.time() - overall_start
            timing_log.append(f"**Total time: {total_time:.3f}s**")

            st.write("Asset %s has been uploaded with Token ID: %d" %
                     (asset.name, token_id))
            st.success(f"✅ Published successfully in {total_time:.3f}s")
            
            with st.expander("Publish Log"):
                for log_entry in timing_log:
                    st.write(log_entry)
                st.write(f"Agreement contract: {owner_agreement}")
        con.close()
