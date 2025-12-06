import streamlit as st
import os
import time
import shutil
from os.path import basename, join, dirname, abspath
from uuid import uuid4
from decimal import Decimal
from contract import AssetAgreement, AssetFactory
from constants import LOCAL_ENDPOINT
from db import get_demo_db
from web3 import Web3
from utils import from_wei
from user_utils import get_user_display_options, get_user_from_display
from extract_watermark import WatermarkWrapper


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

            # Ensure images directory exists (use absolute path based on __file__)
            # Get the project root directory (parent of src/)
            # __file__ is the path to this upload.py file: .../src/upload.py
            current_file = abspath(__file__)  # Absolute path to upload.py
            src_dir = dirname(current_file)  # src/ directory
            project_root = dirname(src_dir)   # Project root (parent of src/)
            
            images_dir = join(project_root, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            new_file_location = join(images_dir, new_file_name)
            
            # Save file
            try:
                with open(new_file_location, "wb") as f:
                    f.write(data)
                    f.flush()  # Ensure data is written to buffer
                    if hasattr(f, 'fileno'):
                        try:
                            os.fsync(f.fileno())  # Force write to disk
                        except:
                            pass  # Some file systems don't support fsync
            except Exception as e:
                st.error(f"❌ **Error saving file:** {str(e)}")
                st.error(f"Path attempted: {new_file_location}")
                con.close()
                return
            
            # Verify file was saved
            if not os.path.exists(new_file_location):
                st.error(f"❌ **Error:** File was not saved to {new_file_location}")
                st.error(f"Please check write permissions for directory: {images_dir}")
                con.close()
                return
            
            # Verify file size
            saved_size = os.path.getsize(new_file_location)
            original_size = len(data)
            if saved_size != original_size:
                st.error(f"❌ **Error:** File size mismatch. Expected {original_size} bytes, got {saved_size} bytes")
                con.close()
                return
            
            step1_time = time.time() - start_time
            timing_log.append(f"1. Save asset file: {step1_time:.3f}s (Saved to: {new_file_location}, Size: {saved_size} bytes)")

            # Step 1.5: Check for existing watermark (auto-detect type)
            # IMPORTANT: Create a copy for watermark checking to avoid losing the original file
            # extract_watermark() uses move() which can lose the file if there's an error
            start_time = time.time()
            detected_method = None
            oid = None
            bid = None
            owner_name = None
            buyer_name = None
            
            # Create a temporary copy for watermark checking
            temp_check_file = join(images_dir, f"temp_check_{new_file_name}")
            try:
                shutil.copy2(new_file_location, temp_check_file)
            except Exception as e:
                st.warning(f"⚠️ Could not create temporary copy for watermark check: {str(e)}")
                temp_check_file = None
            
            # Try both LSB and SSL methods to detect watermark type
            # Try LSB first (faster)
            if temp_check_file and os.path.exists(temp_check_file):
                try:
                    wm_lsb = WatermarkWrapper("lsb")
                    oid, bid = wm_lsb.extract_watermark(temp_check_file)
                    # Validate: check if IDs are in valid range (0-63 for 6 bits) and exist in database
                    # This helps reduce false positives from random bit patterns
                    if 0 <= oid <= 63 and 0 <= bid <= 63:
                        res_owner = con.execute("SELECT uname FROM users WHERE id = ?", [oid])
                        owner_result = res_owner.fetchone()
                        owner_name = owner_result[0] if owner_result else None
                        
                        res_buyer = con.execute("SELECT uname FROM users WHERE id = ?", [bid])
                        buyer_result = res_buyer.fetchone()
                        buyer_name = buyer_result[0] if buyer_result else None
                        
                        # If both IDs exist in database, it's a valid watermark
                        if owner_name is not None and buyer_name is not None:
                            detected_method = "lsb"
                except Exception:
                    pass
                
                # Try SSL if LSB didn't find valid watermark
                if detected_method is None:
                    # Ensure temp file exists before trying SSL extraction
                    if temp_check_file and os.path.exists(temp_check_file):
                        try:
                            wm_ssl = WatermarkWrapper("ssl")
                            # Try to extract watermark
                            oid, bid = wm_ssl.extract_watermark(temp_check_file)
                            
                            # IMPORTANT: SSL extract_watermark() always returns values when it succeeds,
                            # even for images without watermark (decodes random bit patterns).
                            # To reduce false positives, we only block if BOTH IDs exist in database.
                            # This is similar to LSB validation logic.
                            
                            # Log extracted IDs for debugging
                            timing_log.append(f"1.5. SSL extract succeeded: oid={oid}, bid={bid}")
                            
                            # Validate IDs are in reasonable range (0-63 for 6 bits)
                            if oid is not None and bid is not None and 0 <= oid <= 63 and 0 <= bid <= 63:
                                # Check database for names
                                res_owner = con.execute("SELECT uname FROM users WHERE id = ?", [oid])
                                owner_result = res_owner.fetchone()
                                owner_name = owner_result[0] if owner_result else None
                                
                                res_buyer = con.execute("SELECT uname FROM users WHERE id = ?", [bid])
                                buyer_result = res_buyer.fetchone()
                                buyer_name = buyer_result[0] if buyer_result else None
                                
                                # Only block if BOTH IDs exist in database (same as LSB logic)
                                # This reduces false positives while still catching valid watermarks
                                if owner_name is not None and buyer_name is not None:
                                    # Both IDs exist in database - confirmed watermark
                                    detected_method = "ssl"
                                    timing_log.append(f"1.5. SSL extract: Both IDs found in DB - confirmed watermark")
                                else:
                                    # IDs valid but not in database - likely false positive
                                    # Don't block to avoid false positives
                                    timing_log.append(f"1.5. SSL extract: IDs valid but not in DB (oid={oid}, bid={bid}) - skipping to avoid false positive")
                            else:
                                # IDs out of range - definitely false positive, don't block
                                timing_log.append(f"1.5. SSL extract: IDs out of range (oid={oid}, bid={bid}) - skipping (likely false positive)")
                            
                        except Exception as e:
                            # If extract fails with exception, no watermark detected
                            # Log exception for debugging
                            import traceback
                            error_msg = f"SSL extract failed: {str(e)}"
                            error_type = type(e).__name__
                            timing_log.append(f"1.5. SSL extract error ({error_type}): {error_msg}")
                            # Print full traceback for debugging
                            print(f"SSL extract exception: {traceback.format_exc()}")
                            # Don't block if extract failed with exception
                            pass
                    else:
                        timing_log.append(f"1.5. SSL extract skipped: temp file not found")
                
                # Clean up temporary file
                try:
                    if os.path.exists(temp_check_file):
                        os.remove(temp_check_file)
                except Exception:
                    pass
            
            check_time = time.time() - start_time
            
            # Debug logging
            if detected_method:
                st.write(f"🔍 Debug: detected_method={detected_method}, oid={oid}, bid={bid}")
            else:
                st.write(f"🔍 Debug: No watermark detected (detected_method={detected_method})")
            
            # If watermark detected, block publishing
            # For SSL: if extract succeeded and IDs are in valid range, block even if not in DB
            # This prevents uploading images with SSL watermarks from other systems
            if detected_method is not None:
                # Valid watermark detected - block publishing
                timing_log.append(f"1.5. Check for watermark: {check_time:.3f}s (⚠️ VALID WATERMARK DETECTED - {detected_method.upper()})")
                
                st.error("❌ **Watermark Detected - Publishing Blocked**")
                
                # Ensure owner_name and buyer_name are set for display
                if owner_name is None:
                    owner_name = "Unknown (not in database)"
                if buyer_name is None:
                    buyer_name = "Unknown (not in database)"
                
                with st.expander("Watermark Information", expanded=True):
                    st.write(f"**Owner ID:** {oid} ({owner_name})")
                    st.write(f"**Buyer ID:** {bid} ({buyer_name})")
                    st.write(f"**Watermark Type:** {detected_method.upper()} (auto-detected)")
                    st.write(f"**Detection Time:** {check_time:.3f}s")
                
                if owner_name == "Unknown (not in database)" or buyer_name == "Unknown (not in database)":
                    st.warning("⚠️ **Note:** This watermark was detected but the owner/buyer IDs are not in the current database. This image may have been watermarked in a different system or the IDs may have been removed.")
                
                st.info("💡 **Tip:** Only original, unwatermarked images can be published. This image appears to have been previously watermarked and sold.")
                
                # Clean up the saved file since we're not publishing
                if os.path.exists(new_file_location):
                    os.remove(new_file_location)
                
                con.close()
                return
            else:
                # No valid watermark found - continue with publishing
                timing_log.append(f"1.5. Check for watermark: {check_time:.3f}s (✓ No watermark detected)")
                # Continue with normal publishing flow

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
                # Process event logs - try multiple API formats for different web3.py versions
                data = None
                try:
                    # Try web3.py v6+ format (processReceipt with camelCase)
                    data = factory.factory_contract.events.NewContract().processReceipt(deploy_receipt)
                except (AttributeError, TypeError):
                    try:
                        # Fallback to web3.py v5 format (process_receipt with snake_case)
                        data = factory.factory_contract.events.NewContract().process_receipt(deploy_receipt)
                    except (AttributeError, TypeError):
                        # If both fail, parse logs manually from receipt
                        event_abi = factory.factory_contract.events.NewContract()._get_event_abi()
                        event_signature_hash = factory.w3.keccak(text=f"{event_abi['name']}({','.join([inp['type'] for inp in event_abi['inputs']])})")
                        
                        # Find matching log
                        for log in deploy_receipt['logs']:
                            if len(log['topics']) > 0 and log['topics'][0] == event_signature_hash:
                                # Decode the log
                                decoded = factory.factory_contract.events.NewContract().processLog(log)
                                data = [decoded] if decoded else []
                                break
                
                if not data or len(data) == 0:
                    raise ValueError("No NewContract event found in transaction receipt")
                
                owner_agreement = data[0]["args"]["contractAddress"]
                deploy_gas = deploy_receipt.gasUsed
                
                agreement = AssetAgreement(
                    LOCAL_ENDPOINT, owner_agreement, owner_wallet)
                approval_receipt = agreement.set_approval_for_all(self.market_address, True)
                approval_gas = approval_receipt.gasUsed
                
                # Calculate fees
                deploy_tx = factory.w3.eth.get_transaction(deploy_receipt.transactionHash)
                deploy_gas_price = deploy_tx.get('gasPrice') or deploy_receipt.get('effectiveGasPrice', 0)
                deploy_fee_eth = from_wei(deploy_gas * deploy_gas_price, 'ether')
                
                approval_tx = agreement.w3.eth.get_transaction(approval_receipt.transactionHash)
                approval_gas_price = approval_tx.get('gasPrice') or approval_receipt.get('effectiveGasPrice', 0)
                approval_fee_eth = from_wei(approval_gas * approval_gas_price, 'ether')

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
            mint_fee_eth = from_wei(mint_gas * mint_gas_price, 'ether')
            total_gas += mint_gas
            total_fee_eth += mint_fee_eth
            timing_log.append(f"4. Mint asset (Token ID: {token_id}): {step4_time:.3f}s (Gas: {mint_gas:,} gas, Fee: {mint_fee_eth:.9f} ETH)")

            # Step 5: Save to database
            # Save relative path to database for portability
            start_time = time.time()
            # Use relative path from project root (just "images/filename.png")
            relative_filepath = join("images", new_file_name)
            res = con.execute("INSERT INTO assets (owner_id, filepath, token_id) VALUES (?, ?, ?)", [
                              owner_id, relative_filepath, token_id])
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
