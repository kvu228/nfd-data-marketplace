import streamlit as st
from tempfile import NamedTemporaryFile
from os.path import basename
from Crypto.Hash import SHA256
from contract import AssetMarket
from constants import LOCAL_ENDPOINT
from db import get_demo_db
import time


class WatermarkWrapper:
    """
    Wrapper class to switch between SSL and LSB watermarking implementations.
    """
    
    def __init__(self, method: str = "lsb"):
        """
        Initialize watermark wrapper with specified method.
        
        Args:
            method: Watermarking method to use. Options: "lsb" or "ssl". Default: "lsb"
        """
        self.method = method.lower()
        
        if self.method == "ssl":
            from ssl_watermarking.main_multibit import Watermark
        elif self.method == "lsb":
            from lsb_watermarking.main_multibit import Watermark
        else:
            raise ValueError(f"Unknown watermarking method: {method}. Must be 'lsb' or 'ssl'")
        
        self._watermark = Watermark()
    
    def extract_watermark(self, img_filepath: str):
        """Extract watermark from image."""
        return self._watermark.extract_watermark(img_filepath)
    
    def set_watermark(self, owner_id: int, buyer_id: int):
        """Set watermark with owner and buyer IDs."""
        return self._watermark.set_watermark(owner_id, buyer_id)
    
    def watermark_image(self, img_filepath: str):
        """Watermark an image."""
        return self._watermark.watermark_image(img_filepath)
    
    def watermark(self):
        """Watermark batch images."""
        return self._watermark.watermark()
    
    def decode_watermark(self):
        """Decode watermark from batch images."""
        return self._watermark.decode_watermark()


class ExtractWatermark:

    def __init__(self, market_address: str, watermark_method: str = "lsb"):
        """
        Initialize ExtractWatermark.
        
        Args:
            market_address: Address of the market contract
            watermark_method: Watermarking method to use. Options: "lsb" or "ssl". Default: "lsb"
        """
        self.market_address = market_address
        self.watermark_method = watermark_method

    def render_extract_watermark(self):

        st.write("## Identifiability (Detectability): Asset Watermark Extraction")
        st.write("If a watermarked asset is leaked, we can extract the watermark text to find the owner and buyer ID which can then be mapped to their original identity")

        with st.form("extract-wm-form"):
            asset = st.file_uploader("Upload Watermarked Asset")

            upload = st.form_submit_button("Extract Watermark")

            if asset is None or not upload:
                return

            ext = basename(asset.name).split(".")[-1]

            f = NamedTemporaryFile("wb", suffix="." + ext, delete=False)
            f.write(asset.getvalue())
            f.close()
            
            wm = WatermarkWrapper(self.watermark_method)
            timing_log = []
            
            try:
                # Step 1: Extract watermark
                start_time = time.time()
                oid, bid = wm.extract_watermark(f.name)
                extract_time = time.time() - start_time
                timing_log.append(f"1. Extract watermark from image: {extract_time:.3f}s")
                
                # Step 2: Match watermark IDs to database
                start_time = time.time()
                pair = self.process_watermark(oid, bid)
                db_time = time.time() - start_time
                timing_log.append(f"2. Match watermark IDs to Owner and Buyer database: {db_time:.3f}s")
                
                total_time = extract_time + db_time
                st.write("Extracted Watermark: Owner = %s, Buyer = %s " % pair)
                st.success(f"✅ Completed in {total_time:.3f}s")
            except Exception as e:
                st.write("Watermark extraction failed: %s" % str(e))

        with st.expander("Log"):
            for log_entry in timing_log:
                st.write(log_entry)

    def process_watermark(self, owner_id, buyer_id):

        con = get_demo_db()
        res = con.execute("SELECT a.uname, b.uname FROM users AS a INNER JOIN users AS b ON a.id = ? AND b.id = ?", [
                          owner_id, buyer_id])

        data = res.fetchone()
        con.close()

        return data

    def render_recovery(self):

        st.write("## Traceability: Asset Transaction Proof")
        st.write(
            """
        The proof of ownership and the history of ownership can be view on the 
        blockchain using tokenID and the owner ID. In case token ID is not 
        available, we can find the ownership records using the original asset 
        and the IDs.
        """)
        con = get_demo_db()
        with st.form("recovery"):

            res = con.execute("SELECT uname FROM users")

            users = list(map(lambda r: r[0], res.fetchall()))

            original_owner = st.selectbox("Original Owner", options=users)
            asset = st.file_uploader("Upload Original Asset")
            owner = st.selectbox("Seller", options=users)
            buyer = st.selectbox("Buyer", options=users)

            upload = st.form_submit_button("Upload")

            if asset is None or not upload:
                con.close()
                return

            res = con.execute("SELECT a.agreement, b.id, b.wallet, c.id FROM users AS a INNER JOIN users AS b INNER JOIN users as c ON a.uname = ? AND b.uname = ? AND c.uname = ?", [
                              original_owner, owner, buyer])

            owner_agreement, seller_id, seller_wallet, buyer_id = res.fetchone()

            timing_log = []
            
            # Step 1: Compute hash of image
            start_time = time.time()
            cipher = SHA256.new(asset.getvalue())
            cipher.update(bytes([seller_id, buyer_id]))
            img_hash = cipher.digest()
            img_hash_hex = cipher.hexdigest()
            hash_time = time.time() - start_time
            timing_log.append(f"1. Compute hash of image: {hash_time:.3f}s")

            # Step 2: Find sale record
            start_time = time.time()
            market = AssetMarket(
                LOCAL_ENDPOINT, self.market_address, seller_wallet)
            try:
                record = market.get_asset_sale_record(
                    owner_agreement, img_hash)
                record_time = time.time() - start_time
                timing_log.append(f"2. Find sale record with hash: {record_time:.3f}s")
                total_time = hash_time + record_time
                st.write("Owner Address: %s, Buyer Address: %s, Token ID: %d" %
                        (seller_wallet, record[0], record[1]))
                st.success(f"✅ Completed in {total_time:.3f}s")
            except Exception as e:
                record_time = time.time() - start_time
                timing_log.append(f"2. Find sale record (failed): {record_time:.3f}s")
                st.write("Sale Record does not exist")

            with st.expander("Log"):
                for log_entry in timing_log:
                    st.write(log_entry)
                st.write(f"Hash: {img_hash_hex}")
        con.close()

    def render(self):
        self.render_extract_watermark()
        self.render_recovery()
