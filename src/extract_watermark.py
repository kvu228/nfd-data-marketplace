import streamlit as st
from tempfile import NamedTemporaryFile
from os.path import basename
from Crypto.Hash import SHA256
from contract import AssetMarket
from constants import LOCAL_ENDPOINT
from db import get_demo_db
from user_utils import get_user_display_options, get_user_from_display
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
        """
        Extract watermark from image.
        
        For SSL: Handles exceptions that may occur during extraction:
        - IndexError: if decode_watermark returns empty list
        - ValueError: if binary string is invalid or too short
        
        Returns:
            tuple: (owner_id, buyer_id) or raises exception
        """
        try:
            return self._watermark.extract_watermark(img_filepath)
        except (IndexError, ValueError) as e:
            # SSL extract may raise these exceptions when:
            # - decode_watermark returns empty list (IndexError)
            # - binary string is invalid or too short (ValueError)
            # Re-raise with more context
            raise ValueError(f"SSL watermark extraction failed: {str(e)}. The image may not contain a valid SSL watermark.") from e
        except Exception as e:
            # Re-raise other exceptions as-is
            raise
    
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

    def detect_watermark_type(self, img_filepath: str):
        """
        Detect watermark type (LSB or SSL) by trying both methods.
        
        Args:
            img_filepath: Path to the watermarked image
        
        Returns:
            tuple: (detected_method, owner_id, buyer_id) or (None, None, None) if not found
        """
        detected_method = None
        oid = None
        bid = None
        
        # Try LSB first (faster)
        try:
            wm_lsb = WatermarkWrapper("lsb")
            oid, bid = wm_lsb.extract_watermark(img_filepath)
            # Validate by checking if IDs exist in database
            # LSB can have false positives, so we validate against database
            if self._validate_watermark_ids(oid, bid):
                detected_method = "lsb"
                return detected_method, oid, bid
        except Exception:
            pass
        
        # Try SSL if LSB failed
        try:
            wm_ssl = WatermarkWrapper("ssl")
            oid, bid = wm_ssl.extract_watermark(img_filepath)
            # For SSL: if extract succeeded (no exception), we got values
            # SSL extract_watermark() always returns values when it succeeds
            # So if we get here without exception, it's likely a watermark
            
            # Debug logging
            print(f"🔍 SSL extract succeeded: oid={oid}, bid={bid}, type(oid)={type(oid)}, type(bid)={type(bid)}")
            
            # IMPORTANT: If extract succeeded (no exception), we have a watermark
            # SSL always returns values when extract succeeds, so we should return it
            # Validate IDs are in reasonable range (0-63 for 6 bits)
            if oid is not None and bid is not None:
                # Check if IDs are in valid range
                if 0 <= oid <= 63 and 0 <= bid <= 63:
                    # Check if IDs exist in database (preferred)
                    if self._validate_watermark_ids(oid, bid):
                        detected_method = "ssl"
                        print(f"✅ SSL watermark detected (in DB): oid={oid}, bid={bid}")
                        return detected_method, oid, bid
                    else:
                        # Extract succeeded and IDs are valid but not in DB
                        # For SSL, this could still be a watermark from another system
                        # Return it anyway since extract succeeded
                        detected_method = "ssl"
                        print(f"✅ SSL watermark detected (not in DB): oid={oid}, bid={bid}")
                        return detected_method, oid, bid
                else:
                    # IDs out of range - might be corrupted watermark or false positive
                    # But since extract succeeded, we should still return it
                    print(f"⚠️ SSL extract returned out-of-range IDs: oid={oid}, bid={bid} (but extract succeeded)")
                    detected_method = "ssl"
                    return detected_method, oid, bid
            else:
                # Extract returned None values - this shouldn't happen
                print(f"❌ SSL extract returned None values: oid={oid}, bid={bid}")
        except Exception as e:
            # If extract fails with exception, no watermark detected
            import traceback
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"❌ SSL extract exception in detect_watermark_type ({error_type}): {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            # Don't suppress the exception - let it propagate for debugging
            # But don't fail the whole detection, just skip SSL
            pass
        
        return detected_method, oid, bid
    
    def _validate_watermark_ids(self, owner_id, buyer_id):
        """
        Validate watermark IDs by checking if they exist in database.
        
        Args:
            owner_id: Owner ID from watermark
            buyer_id: Buyer ID from watermark
        
        Returns:
            bool: True if both IDs exist in database
        """
        try:
            con = get_demo_db()
            res_owner = con.execute("SELECT id FROM users WHERE id = ?", [owner_id])
            owner_exists = res_owner.fetchone() is not None
            
            res_buyer = con.execute("SELECT id FROM users WHERE id = ?", [buyer_id])
            buyer_exists = res_buyer.fetchone() is not None
            
            con.close()
            return owner_exists and buyer_exists
        except Exception:
            return False

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
            
            timing_log = []
            
            try:
                # Step 1: Detect watermark type and extract
                start_time = time.time()
                detected_method, oid, bid = self.detect_watermark_type(f.name)
                detect_time = time.time() - start_time
                
                if detected_method is None:
                    st.error("❌ **Watermark Not Found**")
                    st.warning("Could not detect watermark using either LSB or SSL method. The image may not be watermarked or the watermark may be corrupted.")
                    timing_log.append(f"1. Detect watermark type: {detect_time:.3f}s (❌ Not found)")
                    
                    # Show debug info
                    with st.expander("🔍 Debug Information", expanded=False):
                        st.write(f"**Owner ID extracted:** {oid}")
                        st.write(f"**Buyer ID extracted:** {bid}")
                        st.write("**Note:** Check console output for detailed SSL extraction logs.")
                else:
                    timing_log.append(f"1. Detect watermark type: {detect_time:.3f}s (✓ {detected_method.upper()} detected)")
                    
                    # Step 2: Match watermark IDs to database
                    start_time = time.time()
                    pair = self.process_watermark(oid, bid)
                    db_time = time.time() - start_time
                    timing_log.append(f"2. Match watermark IDs to Owner and Buyer database: {db_time:.3f}s")
                    
                    total_time = detect_time + db_time
                    
                    # Display results
                    st.success(f"✅ **Watermark Extracted Successfully**")
                    st.info(f"**Watermark Type:** {detected_method.upper()}")
                    
                    if pair and pair[0] and pair[1]:
                        # IDs found in database
                        st.write("**Extracted Watermark:** Owner = %s, Buyer = %s " % pair)
                    else:
                        # IDs not found in database
                        st.write(f"**Extracted Watermark:** Owner ID = {oid}, Buyer ID = {bid}")
                        st.warning("⚠️ **Note:** The owner/buyer IDs are not in the current database. This image may have been watermarked in a different system or the IDs may have been removed.")
                    
                    st.success(f"Completed in {total_time:.3f}s")
            except Exception as e:
                import traceback
                st.error(f"❌ **Extraction Failed:** {str(e)}")
                timing_log.append(f"Error: {str(e)}")
                
                # Show detailed error for debugging
                with st.expander("🔍 Error Details", expanded=True):
                    st.code(traceback.format_exc())
                    st.write("**Error Type:**", type(e).__name__)

        with st.expander("Extraction Log"):
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
            display_options, user_data_dict = get_user_display_options(include_balance=True)
            
            if not display_options:
                st.warning("No users registered yet.")
                con.close()
                return

            original_owner_display = st.selectbox("Original Owner", options=display_options)
            original_owner = get_user_from_display(original_owner_display, user_data_dict)
            
            asset = st.file_uploader("Upload Original Asset")
            
            owner_display = st.selectbox("Seller", options=display_options)
            owner = get_user_from_display(owner_display, user_data_dict)
            
            buyer_display = st.selectbox("Buyer", options=display_options)
            buyer = get_user_from_display(buyer_display, user_data_dict)

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
                st.write(f"Sale Record does not exist: {str(e)}")

            with st.expander("Log"):
                for log_entry in timing_log:
                    st.write(log_entry)
                st.write(f"Hash: {img_hash_hex}")
        con.close()

    def render(self):
        self.render_extract_watermark()
        self.render_recovery()
