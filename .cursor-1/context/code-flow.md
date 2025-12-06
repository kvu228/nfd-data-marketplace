# Code Flow - NFT-Based Data Marketplace

## Tổng Quan Luồng Code

Tài liệu này mô tả chi tiết luồng thực thi code cho các chức năng chính của hệ thống.

## 1. Application Initialization Flow

### Entry Point: `src/app.py`

```python
# Main execution flow
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    app = NFTApp(LOCAL_ETH_ENDPOINT)
    app.render_app()
```

### Initialization Sequence

1. **Create NFTApp instance**
   ```python
   def __init__(self, eth_endpoint: str):
       # 1. Get Web3 provider
       self.web3 = get_web3_provider(eth_endpoint)
       
       # 2. Deploy Market contract (cached)
       self.market_contract_address = AssetMarket.deploy(...)
       
       # 3. Deploy Factory contract (cached)
       self.factory_address = AssetFactory.deploy(...)
       
       # 4. Initialize modules
       self.user_registration = UserRegistration()
       self.upload = Upload(...)
       self.market = Market(...)
       self.extractwm = ExtractWatermark(...)
       self.dasboard = Dashboard(...)
   ```

2. **Contract Deployment (Cached)**
   - `AssetMarket.deploy()` sử dụng decorator `@ContractDeployOnce("market")`
   - Kiểm tra `contracts.json` để xem contract đã deploy chưa
   - Nếu chưa: Deploy mới và lưu address
   - Nếu rồi: Trả về address đã lưu

3. **Render UI**
   - Tạo tabs: User Registration, Dashboard, Publish Asset, Trade, Identifiability/Traceability
   - Mỗi tab gọi render method của module tương ứng

## 2. User Registration Flow

### File: `src/user_registration.py`

### Flow Diagram

```
User Input (name, wallet)
    ↓
UserRegistration.register_user()
    ↓
Check duplicate (name OR wallet)
    ↓
If exists → Error
If not → INSERT INTO users
    ↓
Return success
```

### Code Flow

```python
# 1. User submits form
with st.form("user-register-form"):
    name = st.text_input("Name")
    address = st.text_input("Wallet Address")
    submit = st.form_submit_button("Register")
    
    # 2. Validation
    if len(name) == 0 or len(address) == 0:
        return
    
    # 3. Register user
    if UserRegistration.register_user(name, address):
        st.write("%s has been added!" % name)
    else:
        st.write("Name or Wallet Address already in use!")
```

### Database Operation

```sql
-- Check duplicate
SELECT COUNT(*) FROM users WHERE uname = ? OR wallet = ?

-- Insert new user
INSERT INTO users (uname, wallet) VALUES (?, ?)
```

## 3. Asset Publishing Flow

### File: `src/upload.py`

### Flow Diagram

```
User Uploads File
    ↓
Save to images/ directory
    ↓
Get/Create AssetAgreement Contract
    ↓
Mint NFT (with price, resaleAllowed)
    ↓
Insert to database
    ↓
Display success
```

### Detailed Code Flow

```python
# 1. Form submission
with st.form("asset-upload"):
    owner = st.selectbox("Owner", ...)
    asset = st.file_uploader("Asset")
    price = st.number_input("Price (ETH)")
    resale = st.checkbox("Resale Allowed")
    submit = st.form_submit_button("Publish")
    
    # 2. Save file
    data = asset.getvalue()
    new_file_name = uuid4().hex + "." + ext
    new_file_location = join("images", new_file_name)
    with open(new_file_location, "wb") as f:
        f.write(data)
    
    # 3. Get owner info from database
    res = con.execute("SELECT id, wallet, agreement FROM users WHERE uname = ?", [owner])
    owner_id, owner_wallet, owner_agreement = res.fetchone()
    
    # 4. Create AssetAgreement if not exists
    if owner_agreement is None:
        owner_agreement = AssetFactory(...).deploy_asset_agreement(...)[0]
        agreement = AssetAgreement(..., owner_agreement, owner_wallet)
        agreement.set_approval_for_all(self.market_address, True)
        # Update database
        con.execute("UPDATE users SET agreement = ? WHERE id = ?", ...)
    
    # 5. Mint NFT
    agreement = AssetAgreement(..., owner_agreement, owner_wallet)
    token_id = agreement.get_next_token_id()
    agreement.mint([price], [resale])
    
    # 6. Insert to database
    con.execute("INSERT INTO assets (owner_id, filepath, token_id) VALUES (?, ?, ?)", ...)
    con.commit()
```

### Smart Contract Interaction

```solidity
// AssetAgreement.mint()
function mint(uint256[] memory _prices, bool[] memory _resaleAllowed) {
    uint256 startTokenID = _nextTokenId();
    _mint(msg.sender, _prices.length);  // ERC721A batch mint
    uint256 endTokenID = _nextTokenId();
    
    // Set metadata for each token
    for (uint256 i = startTokenID; i < endTokenID; i++) {
        mintedAssets[i].price = _prices[i - startTokenID];
        mintedAssets[i].forSale = true;
        mintedAssets[i].resaleAllowed = _resaleAllowed[i - startTokenID];
    }
}
```

## 4. Trading Flow

### File: `src/market.py`

### Flow Diagram

```
Buyer Selects Asset
    ↓
Get Asset Info (price, seller)
    ↓
Load Original Image
    ↓
Create Watermark (seller_id, buyer_id)
    ↓
Compute Hash (SHA256)
    ↓
Update Hash on Blockchain
    ↓
Execute Purchase Transaction
    ↓
Transfer Ownership
    ↓
Distribute Payment (Royalty)
    ↓
Download Watermarked Asset
```

### Detailed Code Flow

```python
# 1. Buyer clicks "Buy" button
def on_image_buy(self, agreement_address: str, token_id: int, buyer_id: int):
    # 2. Get asset info from blockchain
    agreement = AssetAgreement(LOCAL_ENDPOINT, agreement_address, ...)
    asset_price = agreement.price_of(token_id)
    seller_address = agreement.owner_of(token_id)
    
    # 3. Get seller_id from database
    res = con.execute("SELECT id FROM users WHERE wallet = ?", [seller_address])
    seller_id, = res.fetchone()
    
    # 4. Load original image
    res = con.execute("SELECT assets.filepath FROM ... WHERE ...", ...)
    img_location, = res.fetchone()
    
    # 5. Create temporary file and compute hash
    wm_image = NamedTemporaryFile("wb", suffix=".png", delete=False)
    with open(img_location, "rb") as f:
        data = f.read()
        wm_image.write(data)
        cipher = SHA256.new(data)
        cipher.update(bytes([seller_id, buyer_id]))
        img_hash = cipher.digest()
    
    wm_file_name = wm_image.name
    wm_image.close()
    
    # 6. Watermark image
    wm = Watermark()
    wm.set_watermark(seller_id, buyer_id)
    wm.watermark_image(wm_file_name)
    
    # 7. Update hash on blockchain (as market manager)
    asset_market_manager = AssetMarket(..., self.manager_address)
    asset_market_manager.update_hash(agreement_address, token_id, img_hash)
    
    # 8. Execute purchase (as buyer)
    res = con.execute("SELECT wallet FROM users WHERE id = ?", [buyer_id])
    buyer_wallet_address, = res.fetchone()
    
    asset_market = AssetMarket(..., buyer_wallet_address)
    asset_market.purchase(agreement_address, token_id, asset_price)
    
    # 9. Provide download
    with open(wm_file_name, "rb") as f:
        st.download_button("Verify Signature and Download Asset", f, ...)
```

### Watermarking Process

```python
# LSB Watermarking
class Watermark:
    def set_watermark(self, owner_id: int, buyer_id: int):
        # Convert to binary (6 bits each)
        owner_bin = bin(owner_id)[2:].zfill(8)[2:]  # 6 bits
        buyer_bin = bin(buyer_id)[2:].zfill(8)[2:]  # 6 bits
        watermark_bin = owner_bin + buyer_bin  # 12 bits total
        
        # Save to temp file
        t = NamedTemporaryFile("w", delete=False)
        t.write(watermark_bin)
        self.msg_path = t.name
    
    def watermark_image(self, img_filepath: str):
        # Move image to input directory
        # Process watermarking
        # Move watermarked image back
```

### Smart Contract Purchase Flow

```solidity
// AssetMarket.purchase()
function purchase(address _agreement, uint256 _tokenId) public payable {
    IAssetAgreement agreementContract = IAssetAgreement(_agreement);
    
    // 1. Validate price
    uint256 price = agreementContract.priceOf(_tokenId);
    require(msg.value >= price, "Not enough ETH!");
    
    // 2. Check sale status
    require(agreementContract.isForSale(_tokenId), "Asset is not for sale");
    
    // 3. Get current owner
    address assetOwner = agreementContract.ownerOf(_tokenId);
    
    // 4. Transfer NFT
    agreementContract.transferFrom(assetOwner, msg.sender, _tokenId);
    agreementContract.updateSaleStatus(_tokenId, false);
    
    // 5. Process payment with royalty
    processPayment(
        agreementContract.getOwner(),  // original owner
        assetOwner,                    // current seller
        agreementContract.getOwnerRoyalty()
    );
    
    emit Purchase(assetOwner, msg.sender, _tokenId, price);
}
```

### Payment Distribution

```solidity
function processPayment(address _originalOwner, address _seller, uint256 _ownerRoyalty) {
    // 1. Calculate market cut
    uint256 marketCut = (msg.value * marketRoyalty) / 1 ether;
    uint256 remaining = msg.value - marketCut;
    
    // 2. Distribute based on seller
    if (_originalOwner == _seller) {
        // Direct sale: all to original owner
        payable(_originalOwner).transfer(remaining);
    } else {
        // Resale: split between original owner and seller
        uint256 ownerCut = (remaining * _ownerRoyalty) / 1 ether;
        payable(_originalOwner).transfer(ownerCut);
        payable(_seller).transfer(remaining - ownerCut);
    }
}
```

## 5. Watermark Extraction Flow

### File: `src/extract_watermark.py`

### Flow Diagram

```
Upload Watermarked Image
    ↓
Extract Watermark (owner_id, buyer_id)
    ↓
Query Database for User Names
    ↓
Display Result
```

### Code Flow

```python
# 1. User uploads watermarked image
with st.form("extract-wm-form"):
    asset = st.file_uploader("Upload Watermarked Asset")
    upload = st.form_submit_button("Extract Watermark")
    
    # 2. Save to temp file
    f = NamedTemporaryFile("wb", suffix="." + ext, delete=False)
    f.write(asset.getvalue())
    f.close()
    
    # 3. Extract watermark
    wm = Watermark()
    try:
        oid, bid = wm.extract_watermark(f.name)
        
        # 4. Map IDs to names
        pair = self.process_watermark(oid, bid)
        st.write("Extracted Watermark: Owner = %s, Buyer = %s " % pair)
    except Exception as e:
        st.write("Watermark extraction failed: %s" % str(e))
```

### Watermark Extraction Process

```python
# LSB Decoding
def extract_watermark(self, img_filepath: str):
    # 1. Load image
    img = Image.open(img_filepath)
    img_array = np.array(img)
    
    # 2. Extract LSBs
    img_flat = img_array.flatten()
    watermark_bits = []
    for i in range(12):  # 12 bits
        watermark_bits.append(img_flat[i] & 1)
    
    # 3. Convert to IDs
    wm_str = ''.join(map(str, watermark_bits))
    oid = int(wm_str[:6], 2)   # First 6 bits
    bid = int(wm_str[6:], 2)   # Last 6 bits
    
    return oid, bid
```

## 6. Hash-based Traceability Flow

### File: `src/extract_watermark.py`

### Flow Diagram

```
Upload Original Image + IDs
    ↓
Compute Hash (SHA256 with IDs)
    ↓
Query Blockchain (getAssetSaleRecord)
    ↓
Display Transaction Record
```

### Code Flow

```python
# 1. User inputs
with st.form("recovery"):
    original_owner = st.selectbox("Original Owner", ...)
    asset = st.file_uploader("Upload Original Asset")
    owner = st.selectbox("Seller", ...)
    buyer = st.selectbox("Buyer", ...)
    
    # 2. Get IDs from database
    res = con.execute("SELECT a.agreement, b.id, b.wallet, c.id FROM ...", ...)
    owner_agreement, seller_id, seller_wallet, buyer_id = res.fetchone()
    
    # 3. Compute hash
    cipher = SHA256.new(asset.getvalue())
    cipher.update(bytes([seller_id, buyer_id]))
    img_hash = cipher.digest()
    
    # 4. Query blockchain
    market = AssetMarket(..., seller_wallet)
    try:
        record = market.get_asset_sale_record(owner_agreement, img_hash)
        # record = (buyer_address, token_id)
        st.write("Owner Address: %s, Buyer Address: %s, Token ID: %d" % ...)
    except:
        st.write("Sale Record does not exist")
```

### Blockchain Query

```solidity
// AssetMarket.getAssetSaleRecord()
function getAssetSaleRecord(address _agreement, bytes32 _hash) 
    public view returns (address, uint256) 
{
    IAssetAgreement agreement = IAssetAgreement(_agreement);
    return agreement.getOwnerOfAssetFromHash(_hash);
}

// AssetAgreement.getOwnerOfAssetFromHash()
function getOwnerOfAssetFromHash(bytes32 _hash) 
    public view returns (address, uint256) 
{
    uint256 tokenID = hashRecord[_hash];
    require(_exists(tokenID), "Asset Token ID does not exist");
    require(mintedAssets[tokenID].assetHash == _hash, "Asset Hash does not exist");
    return (ownerOf(tokenID), tokenID);
}
```

## 7. Dashboard Flow

### File: `src/dashboard.py`

### Flow Diagram

```
User Selects Account
    ↓
Query Assets Owned by User
    ↓
Display Assets with Metadata
    ↓
Toggle Sale Status (if resale allowed)
```

### Code Flow

```python
# 1. User selection
user = st.selectbox("User", ...)
res = con.execute("SELECT users.wallet FROM users WHERE users.uname = ?", [user])
selected_user_wallet, = res.fetchone()

# 2. Query all assets
res = con.execute("SELECT users.uname, users.agreement, assets.filepath, assets.token_id FROM ...")
images = res.fetchall()

# 3. Filter and display
for (user_name, user_agreement, asset_filepath, asset_token_id) in images:
    agreement = AssetAgreement(..., user_agreement, selected_user_wallet)
    
    # Get metadata
    price, assetHash, forSale, resaleAllowed = agreement.fetch_asset_metadata(asset_token_id)
    
    # Check ownership
    if selected_user_wallet != agreement.owner_of(asset_token_id):
        continue
    
    # Display asset
    st.image(pil_img, "Original Owner: %s. Price (%f ETH). Resale: %r. For Sale: %r" % ...)
    
    # Toggle sale status
    sale_status = st.button("Toggle Sale Status", disabled=not resaleAllowed)
    if sale_status:
        new_sale_status = not forSale
        market = AssetMarket(..., selected_user_wallet)
        market.update_sale_status(user_agreement, asset_token_id, new_sale_status)
```

## 8. Contract Deployment Flow

### File: `src/contract.py`

### Flow Diagram

```
Check contracts.json
    ↓
If contract exists → Return cached address
    ↓
If not → Deploy new contract
    ↓
Save address to contracts.json
    ↓
Return address
```

### Code Flow

```python
@ContractDeployOnce("market")
def deploy(http_endpoint: str, wallet_address: str = None):
    # 1. Check cache
    try:
        f = open("contracts.json", "r")
        contract_data = loads(f.read())
        f.close()
    except:
        contract_data = dict()
    
    # 2. If cached, return
    if contract_name in contract_data:
        return contract_data[contract_name]
    
    # 3. Deploy new contract
    w3 = get_web3_provider(http_endpoint)
    w3.eth.default_account = wallet_address
    
    w3_contract = w3.eth.contract(
        abi=get_market_abi(), 
        bytecode=get_market_bytecode()
    )
    
    tx_hash = Contract.send_contract_call(w3_contract.constructor())
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    
    # 4. Save to cache
    contract_data[contract_name] = (tx_receipt.contractAddress, tx_receipt.gasUsed)
    
    f = open("contracts.json", "w")
    f.write(dumps(contract_data))
    f.close()
    
    return contract_data[contract_name]
```

## 9. Transaction Signing Flow

### File: `src/contract.py`

### Code Flow

```python
@staticmethod
def send_contract_call(call, value: float = None):
    if Contract.PRIVATE_KEY is not None:
        # 1. Build transaction
        txn = call.buildTransaction() if value is None else call.buildTransaction({
            "value": Web3.toWei(value, "ether")
        })
        
        # 2. Get account address
        account_address = Contract.W3_PROVIDER.eth.account.from_key(
            Contract.PRIVATE_KEY).address
        
        # 3. Set nonce
        if Contract.NONCE is None:
            Contract.NONCE = Contract.W3_PROVIDER.eth.get_transaction_count(account_address)
        else:
            Contract.NONCE += 1
        txn["nonce"] = Contract.NONCE
        
        # 4. Sign transaction
        signed_txn = Contract.W3_PROVIDER.eth.account.sign_transaction(
            txn, Contract.PRIVATE_KEY)
        
        # 5. Send transaction
        return Contract.W3_PROVIDER.eth.send_raw_transaction(signed_txn.rawTransaction)
    else:
        # Local node: use default account
        return call.transact({'value': Web3.toWei(value, "ether")}) if value is not None else call.transact()
```

## Error Handling

### Common Error Scenarios

1. **Contract Not Deployed**: Check `contracts.json` và deploy nếu cần
2. **Insufficient Funds**: Validate balance trước khi purchase
3. **Asset Not For Sale**: Check `isForSale` status
4. **Watermark Extraction Failed**: Try-catch trong extract_watermark
5. **Database Errors**: Transaction rollback nếu cần

### Transaction Revert Handling

```python
try:
    tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    # Check for revert
    if tx_receipt.status == 0:
        raise Exception("Transaction reverted")
except Exception as e:
    st.error(f"Transaction failed: {str(e)}")
```

## Performance Considerations

1. **Contract Caching**: Deploy once, reuse address
2. **Database Connections**: Reuse connections khi có thể
3. **Image Processing**: Resize images trước khi display
4. **Blockchain Calls**: Batch calls khi có thể
5. **Watermarking**: Process asynchronously nếu cần

