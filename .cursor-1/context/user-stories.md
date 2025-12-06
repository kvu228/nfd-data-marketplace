# User Stories - NFT-Based Data Marketplace

Tài liệu này mô tả các user stories từ các trường hợp đơn giản (happy cases) đến các trường hợp phức tạp (complex cases) trong hệ thống NFT-Based Data Marketplace.

## Mục Lục

1. [Simple Happy Cases](#simple-happy-cases)
2. [Medium Complexity Cases](#medium-complexity-cases)
3. [Complex Cases](#complex-cases)
4. [Error Cases](#error-cases)

---

## Simple Happy Cases

### Story 1: User Registration (Đăng ký người dùng)

**As a** new user  
**I want to** register with my name and wallet address  
**So that** I can participate in the marketplace

**Acceptance Criteria:**
- User provides unique name and wallet address
- System validates uniqueness (name OR wallet must be unique)
- User is saved to database
- Success message is displayed

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant UR as UserRegistration
    participant DB as SQLite Database

    User->>UI: Enter name and wallet address
    User->>UI: Click "Register"
    UI->>UR: register_user(name, address)
    UR->>DB: SELECT COUNT(*) WHERE uname=? OR wallet=?
    DB-->>UR: count = 0
    UR->>DB: INSERT INTO users (uname, wallet)
    DB-->>UR: Success
    UR-->>UI: True
    UI-->>User: "User has been added!"
```

**Flow:**
1. User fills registration form
2. System checks for duplicates
3. If no duplicate, insert new user
4. Display success message

---

### Story 2: Simple Asset Publishing (Xuất bản tài sản đơn giản)

**As a** registered owner  
**I want to** publish an asset with price and resale settings  
**So that** buyers can purchase it

**Preconditions:**
- Owner already has AssetAgreement contract deployed
- Owner is registered in system

**Acceptance Criteria:**
- Asset file is saved to local storage
- NFT is minted with price and resaleAllowed metadata
- Asset record is saved to database
- Token ID is displayed

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Owner
    participant UI as Streamlit UI
    participant Upload as Upload Module
    participant FS as File System
    participant AA as AssetAgreement Contract
    participant BC as Blockchain
    participant DB as Database

    Owner->>UI: Select owner, upload file, set price
    Owner->>UI: Click "Publish"
    UI->>Upload: render() with form data
    Upload->>FS: Save file to images/
    FS-->>Upload: File saved
    Upload->>DB: SELECT owner info
    DB-->>Upload: owner_id, wallet, agreement_address
    Upload->>AA: mint([price], [resaleAllowed])
    AA->>BC: Mint NFT transaction
    BC-->>AA: Token ID
    AA-->>Upload: Mint receipt
    Upload->>DB: INSERT INTO assets
    DB-->>Upload: Success
    Upload-->>UI: Success with Token ID
    UI-->>Owner: "Asset published with Token ID: X"
```

**Flow:**
1. Owner uploads file and sets metadata
2. File saved to local storage
3. Get owner's existing AssetAgreement contract
4. Mint NFT with metadata
5. Save asset record to database
6. Display success with Token ID

---

### Story 3: Simple Purchase (Mua tài sản đơn giản)

**As a** buyer  
**I want to** purchase an asset from the marketplace  
**So that** I own the watermarked asset

**Preconditions:**
- Buyer is registered
- Asset is for sale
- Buyer has sufficient ETH balance

**Acceptance Criteria:**
- Watermark is applied to asset
- Hash is computed and stored on blockchain
- NFT ownership is transferred
- Payment is distributed correctly
- Watermarked asset is downloadable

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Buyer
    participant UI as Streamlit UI
    participant Market as Market Module
    participant WM as Watermark Module
    participant FS as File System
    participant AA as AssetAgreement Contract
    participant AM as AssetMarket Contract
    participant BC as Blockchain
    participant DB as Database

    Buyer->>UI: Select asset and click "Buy"
    UI->>Market: on_image_buy(agreement, token_id, buyer_id)
    Market->>AA: price_of(token_id)
    AA-->>Market: asset_price
    Market->>AA: owner_of(token_id)
    AA-->>Market: seller_address
    Market->>DB: SELECT seller_id WHERE wallet=?
    DB-->>Market: seller_id
    Market->>FS: Load original image
    FS-->>Market: Image data
    Market->>Market: Compute hash(SHA256(image + seller_id + buyer_id))
    Market->>WM: set_watermark(seller_id, buyer_id)
    Market->>WM: watermark_image(file)
    WM-->>Market: Watermarked image
    Market->>AM: update_hash(agreement, token_id, hash)
    AM->>BC: Update hash transaction
    BC-->>AM: Receipt
    Market->>AM: purchase(agreement, token_id, price)
    AM->>AA: transferFrom(seller, buyer, token_id)
    AA->>BC: Transfer NFT
    AM->>AM: processPayment(royalty distribution)
    BC-->>AM: Purchase receipt
    Market-->>UI: Success with download link
    UI-->>Buyer: Download watermarked asset
```

**Flow:**
1. Buyer selects asset and clicks Buy
2. Get asset info from blockchain
3. Load original image
4. Create watermark with seller_id and buyer_id
5. Compute hash of watermarked asset
6. Update hash on blockchain
7. Execute purchase transaction
8. Transfer NFT ownership
9. Distribute payment (royalty)
10. Provide download link

---

## Medium Complexity Cases

### Story 4: Asset Publishing with Contract Creation (Xuất bản với tạo contract mới)

**As a** new owner  
**I want to** publish my first asset  
**So that** the system creates my AssetAgreement contract automatically

**Preconditions:**
- Owner is registered but has no AssetAgreement contract yet

**Acceptance Criteria:**
- AssetAgreement contract is deployed via Factory
- Contract address is saved to user record
- Approval is set for Market contract
- NFT is minted successfully

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Owner
    participant UI as Streamlit UI
    participant Upload as Upload Module
    participant FS as File System
    participant AF as AssetFactory Contract
    participant AA as AssetAgreement Contract
    participant AM as AssetMarket Contract
    participant BC as Blockchain
    participant DB as Database

    Owner->>UI: Upload asset (first time)
    UI->>Upload: render() with form data
    Upload->>FS: Save file
    Upload->>DB: SELECT owner info
    DB-->>Upload: owner_id, wallet, agreement=NULL
    Upload->>AF: createNewAssetAgreement(name, symbol, market)
    AF->>BC: Deploy AssetAgreement contract
    BC-->>AF: Contract address
    AF-->>Upload: agreement_address
    Upload->>AA: set_approval_for_all(market, true)
    AA->>BC: Approval transaction
    BC-->>AA: Receipt
    Upload->>DB: UPDATE users SET agreement=?
    DB-->>Upload: Success
    Upload->>AA: mint([price], [resaleAllowed])
    AA->>BC: Mint NFT
    BC-->>AA: Token ID
    Upload->>DB: INSERT INTO assets
    Upload-->>UI: Success with Token ID
    UI-->>Owner: "Asset published"
```

**Flow:**
1. Owner uploads first asset
2. System detects no AssetAgreement contract
3. Deploy new contract via Factory
4. Set approval for Market contract
5. Update user record with contract address
6. Mint NFT
7. Save asset record

---

### Story 5: Resale Scenario (Kịch bản bán lại)

**As a** buyer who purchased an asset  
**I want to** resell the asset I bought  
**So that** I can profit from the resale

**Preconditions:**
- Buyer owns an asset
- Asset has resaleAllowed = true
- Asset is currently not for sale

**Acceptance Criteria:**
- Owner can toggle sale status
- Asset appears in marketplace when forSale = true
- Resale includes royalty to original owner
- Payment is split correctly between original owner and seller

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Owner as Current Owner
    participant UI as Streamlit UI
    participant Dashboard as Dashboard Module
    participant AA as AssetAgreement Contract
    participant AM as AssetMarket Contract
    participant BC as Blockchain
    participant Buyer as New Buyer
    participant Market as Market Module

    Owner->>UI: View Dashboard
    UI->>Dashboard: render()
    Dashboard->>AA: fetch_asset_metadata(token_id)
    AA-->>Dashboard: price, hash, forSale=false, resaleAllowed=true
    Owner->>UI: Click "Toggle Sale Status"
    UI->>AM: update_sale_status(agreement, token_id, true)
    AM->>AA: updateSaleStatus(token_id, true)
    AA->>BC: Update sale status transaction
    BC-->>AM: Receipt
    Note over Owner,Buyer: Asset now appears in marketplace
    Buyer->>UI: Select asset and click "Buy"
    UI->>Market: on_image_buy(...)
    Market->>AM: purchase(agreement, token_id, price)
    AM->>AM: processPayment(originalOwner, currentOwner, royalty)
    AM->>AM: Calculate: marketCut, ownerCut, sellerCut
    AM->>BC: Transfer to original owner (royalty)
    AM->>BC: Transfer to current owner (remaining)
    AM->>BC: Transfer NFT to buyer
    BC-->>AM: Purchase receipt
    Market-->>UI: Success
    UI-->>Buyer: Download watermarked asset
```

**Flow:**
1. Owner views dashboard
2. Owner toggles sale status to true
3. Asset appears in marketplace
4. New buyer purchases asset
5. Payment is distributed:
   - Market cut
   - Original owner royalty
   - Current seller (remaining)
6. NFT transferred to new buyer

---

### Story 6: Watermark Extraction (Trích xuất watermark)

**As a** marketplace operator or investigator  
**I want to** extract watermark from a leaked asset  
**So that** I can identify the original owner and buyer

**Preconditions:**
- Watermarked asset file is available
- Asset was purchased through marketplace

**Acceptance Criteria:**
- Watermark is extracted successfully
- Owner ID and Buyer ID are identified
- IDs are mapped to user names from database
- Result is displayed

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Investigator
    participant UI as Streamlit UI
    participant Extract as ExtractWatermark Module
    participant WM as Watermark Module
    participant DB as Database

    Investigator->>UI: Upload watermarked asset
    Investigator->>UI: Click "Extract Watermark"
    UI->>Extract: render_extract_watermark()
    Extract->>WM: extract_watermark(image_path)
    WM->>WM: Load image
    WM->>WM: Extract LSB bits (12 bits)
    WM->>WM: Decode owner_id (6 bits) and buyer_id (6 bits)
    WM-->>Extract: (owner_id, buyer_id)
    Extract->>DB: SELECT uname WHERE id IN (owner_id, buyer_id)
    DB-->>Extract: (owner_name, buyer_name)
    Extract-->>UI: Display result
    UI-->>Investigator: "Owner: X, Buyer: Y"
```

**Flow:**
1. Upload watermarked asset
2. Extract watermark using LSB/SSL algorithm
3. Decode owner_id and buyer_id
4. Query database for user names
5. Display mapping result

---

## Complex Cases

### Story 7: Hash-based Traceability (Truy vết dựa trên hash)

**As a** marketplace operator  
**I want to** trace asset ownership history using hash  
**So that** I can verify transaction records on blockchain

**Preconditions:**
- Original asset file is available
- Seller and buyer IDs are known
- Transaction was recorded on blockchain

**Acceptance Criteria:**
- Hash is computed correctly
- Blockchain query returns sale record
- Token ID and addresses are displayed
- Handles case when record doesn't exist

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Operator
    participant UI as Streamlit UI
    participant Extract as ExtractWatermark Module
    participant DB as Database
    participant AM as AssetMarket Contract
    participant AA as AssetAgreement Contract
    participant BC as Blockchain

    Operator->>UI: Upload original asset, select users
    Operator->>UI: Click "Upload"
    UI->>Extract: render_recovery()
    Extract->>DB: SELECT agreement, seller_id, seller_wallet, buyer_id
    DB-->>Extract: agreement_address, seller_id, seller_wallet, buyer_id
    Extract->>Extract: Compute SHA256(asset + seller_id + buyer_id)
    Extract->>AM: get_asset_sale_record(agreement, hash)
    AM->>AA: getOwnerOfAssetFromHash(hash)
    AA->>BC: Query hashRecord[hash]
    BC-->>AA: token_id
    AA->>AA: Verify hash matches
    AA->>AA: Get ownerOf(token_id)
    AA-->>AM: (buyer_address, token_id)
    AM-->>Extract: Sale record
    Extract-->>UI: Display transaction info
    UI-->>Operator: "Owner: X, Buyer: Y, Token ID: Z"
```

**Flow:**
1. Upload original asset and select users
2. Get agreement address and user IDs from database
3. Compute hash (SHA256 of asset + seller_id + buyer_id)
4. Query blockchain for sale record
5. Contract verifies hash exists and returns token info
6. Display transaction record

---

### Story 8: Multi-step Transaction Flow (Luồng giao dịch nhiều bước)

**As a** buyer  
**I want to** complete a purchase transaction  
**So that** all steps (watermarking, hash update, payment) are executed atomically

**Preconditions:**
- Asset is for sale
- Buyer has sufficient balance
- All contracts are properly configured

**Acceptance Criteria:**
- All steps complete successfully
- If any step fails, transaction is rolled back
- Gas costs are tracked
- Timing information is logged

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Buyer
    participant UI as Streamlit UI
    participant Market as Market Module
    participant FS as File System
    participant WM as Watermark Module
    participant AM as AssetMarket Contract
    participant AA as AssetAgreement Contract
    participant BC as Blockchain
    participant DB as Database

    Buyer->>UI: Click "Buy"
    UI->>Market: on_image_buy()
    
    Note over Market: Step 1: Get Agreement Info
    Market->>AA: price_of(), owner_of()
    AA-->>Market: price, seller_address
    Market->>DB: Get seller_id
    DB-->>Market: seller_id
    
    Note over Market: Step 2: Load & Hash Image
    Market->>FS: Load original image
    FS-->>Market: Image data
    Market->>Market: Compute hash(SHA256)
    
    Note over Market: Step 3: Watermark Image
    Market->>WM: set_watermark(seller_id, buyer_id)
    Market->>WM: watermark_image()
    WM-->>Market: Watermarked file
    
    Note over Market: Step 4: Update Hash on Blockchain
    Market->>AM: update_hash(agreement, token_id, hash)
    AM->>AA: updateHash(token_id, hash)
    AA->>BC: Transaction
    BC-->>AM: Receipt (gas tracked)
    
    Note over Market: Step 5: Execute Purchase
    Market->>AM: purchase(agreement, token_id, price)
    AM->>AA: transferFrom(seller, buyer, token_id)
    AM->>AM: processPayment(royalty)
    AM->>BC: Transfer NFT + Payment transactions
    BC-->>AM: Receipt (gas tracked)
    
    Note over Market: Step 6: Provide Download
    Market->>FS: Read watermarked file
    FS-->>Market: File data
    Market-->>UI: Success + Download link + Timing log
    UI-->>Buyer: Display results with gas costs
```

**Flow:**
1. Get agreement and seller info
2. Load image and compute hash
3. Apply watermark
4. Update hash on blockchain (track gas)
5. Execute purchase transaction (track gas)
6. Provide download link
7. Display timing and gas information

---

### Story 9: Dashboard Asset Management (Quản lý tài sản trên Dashboard)

**As a** user  
**I want to** view all my owned assets and manage their sale status  
**So that** I can control which assets are available for purchase

**Preconditions:**
- User is registered
- User owns at least one asset

**Acceptance Criteria:**
- All owned assets are displayed
- Asset metadata is shown (price, resale status, sale status)
- User can toggle sale status if resale is allowed
- Changes are reflected on blockchain

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Dashboard as Dashboard Module
    participant DB as Database
    participant AA as AssetAgreement Contract
    participant AM as AssetMarket Contract
    participant BC as Blockchain

    User->>UI: Select user from dropdown
    UI->>Dashboard: render()
    Dashboard->>DB: SELECT users, assets JOIN
    DB-->>Dashboard: All assets with owner info
    loop For each asset
        Dashboard->>AA: fetch_asset_metadata(token_id)
        AA-->>Dashboard: price, hash, forSale, resaleAllowed
        Dashboard->>AA: owner_of(token_id)
        AA-->>Dashboard: current_owner
        alt User owns asset
            Dashboard->>UI: Display asset with metadata
            User->>UI: Click "Toggle Sale Status"
            UI->>AM: update_sale_status(agreement, token_id, new_status)
            AM->>AA: updateSaleStatus(token_id, new_status)
            AA->>BC: Update transaction
            BC-->>AM: Receipt
            AM->>AA: set_approval_for_all(market, true)
            AA->>BC: Approval transaction
            BC-->>AA: Receipt
            Dashboard-->>UI: Success message
        else User doesn't own
            Note over Dashboard: Skip asset
        end
    end
    UI-->>User: Display all owned assets
```

**Flow:**
1. User selects their account
2. Query all assets from database
3. For each asset:
   - Get metadata from blockchain
   - Check ownership
   - Display if owned
4. User can toggle sale status
5. Update blockchain and set approvals
6. Refresh display

---

### Story 10: Contract Deployment Caching (Cache deployment contract)

**As a** system administrator  
**I want to** ensure contracts are deployed only once  
**So that** we don't waste gas and maintain consistency

**Preconditions:**
- System is starting up
- contracts.json may or may not exist

**Acceptance Criteria:**
- Check contracts.json for existing addresses
- Deploy only if not cached
- Save new addresses to cache
- Return cached address if exists

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant App as NFTApp
    participant Contract as Contract Module
    participant Cache as contracts.json
    participant BC as Blockchain

    App->>Contract: AssetMarket.deploy()
    Contract->>Cache: Read contracts.json
    alt Contract exists in cache
        Cache-->>Contract: market_address
        Contract-->>App: Cached address
    else Contract not in cache
        Contract->>BC: Deploy AssetMarket contract
        BC-->>Contract: contract_address, gasUsed
        Contract->>Cache: Write to contracts.json
        Cache-->>Contract: Success
        Contract-->>App: New address
    end
    
    App->>Contract: AssetFactory.deploy()
    Contract->>Cache: Read contracts.json
    alt Factory exists in cache
        Cache-->>Contract: factory_address
        Contract-->>App: Cached address
    else Factory not in cache
        Contract->>BC: Deploy AssetFactory contract
        BC-->>Contract: contract_address, gasUsed
        Contract->>Cache: Write to contracts.json
        Cache-->>App: New address
    end
```

**Flow:**
1. App initialization requests contract deployment
2. Check contracts.json cache
3. If cached, return address
4. If not cached, deploy new contract
5. Save address to cache
6. Return address

---

## Error Cases

### Story 11: Duplicate User Registration (Đăng ký trùng lặp)

**As a** user  
**I want to** see an error message when registering with duplicate name or wallet  
**So that** I know why registration failed

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant UR as UserRegistration
    participant DB as Database

    User->>UI: Enter duplicate name/wallet
    User->>UI: Click "Register"
    UI->>UR: register_user(name, address)
    UR->>DB: SELECT COUNT(*) WHERE uname=? OR wallet=?
    DB-->>UR: count > 0
    UR-->>UI: False
    UI-->>User: "Name or Wallet Address already in use!"
```

---

### Story 12: Insufficient Balance Purchase (Mua không đủ số dư)

**As a** buyer  
**I want to** see an error when I don't have enough ETH  
**So that** I know the transaction failed

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Buyer
    participant UI as Streamlit UI
    participant Market as Market Module
    participant AM as AssetMarket Contract
    participant AA as AssetAgreement Contract
    participant BC as Blockchain

    Buyer->>UI: Click "Buy" (insufficient balance)
    UI->>Market: on_image_buy()
    Market->>AA: price_of(token_id)
    AA-->>Market: price = 1 ETH
    Market->>AM: purchase(agreement, token_id, price)
    AM->>AM: Check msg.value >= price
    AM->>BC: Transaction (reverts)
    BC-->>AM: Revert: "Not enough ETH!"
    AM-->>Market: Exception
    Market-->>UI: Error message
    UI-->>Buyer: "Transaction failed: Not enough ETH!"
```

---

### Story 13: Asset Not For Sale (Tài sản không bán)

**As a** buyer  
**I want to** see that an asset is not available for purchase  
**So that** I don't attempt invalid transactions

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Buyer
    participant UI as Streamlit UI
    participant Market as Market Module
    participant AA as AssetAgreement Contract

    Buyer->>UI: View marketplace
    UI->>Market: render()
    Market->>AA: fetch_asset_metadata(token_id)
    AA-->>Market: forSale = false
    Market->>UI: Skip asset (not displayed)
    Note over Buyer: Asset doesn't appear in marketplace
```

---

### Story 14: Watermark Extraction Failure (Lỗi trích xuất watermark)

**As a** investigator  
**I want to** see an error when watermark extraction fails  
**So that** I know the file may not be watermarked or is corrupted

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Investigator
    participant UI as Streamlit UI
    participant Extract as ExtractWatermark Module
    participant WM as Watermark Module

    Investigator->>UI: Upload corrupted/non-watermarked file
    Investigator->>UI: Click "Extract Watermark"
    UI->>Extract: render_extract_watermark()
    Extract->>WM: extract_watermark(image_path)
    WM->>WM: Try to extract LSB bits
    WM-->>Extract: Exception (corrupted/invalid)
    Extract-->>UI: Exception message
    UI-->>Investigator: "Watermark extraction failed: [error]"
```

---

### Story 15: Hash Record Not Found (Không tìm thấy hash record)

**As a** operator  
**I want to** see a message when hash record doesn't exist  
**So that** I know the transaction may not have occurred

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Operator
    participant UI as Streamlit UI
    participant Extract as ExtractWatermark Module
    participant AM as AssetMarket Contract
    participant AA as AssetAgreement Contract
    participant BC as Blockchain

    Operator->>UI: Upload asset with wrong IDs
    Operator->>UI: Click "Upload"
    UI->>Extract: render_recovery()
    Extract->>Extract: Compute hash
    Extract->>AM: get_asset_sale_record(agreement, hash)
    AM->>AA: getOwnerOfAssetFromHash(hash)
    AA->>BC: Query hashRecord[hash]
    BC-->>AA: hashRecord[hash] = 0 (not found)
    AA-->>AM: Revert: "Asset Hash does not exist"
    AM-->>Extract: Exception
    Extract-->>UI: Error message
    UI-->>Operator: "Sale Record does not exist"
```

---

## Summary of User Stories

### Simple Cases (Stories 1-3)
- Basic CRUD operations
- Single-step transactions
- Direct user interactions

### Medium Cases (Stories 4-6)
- Multi-step processes
- Contract creation
- Resale scenarios
- Watermark extraction

### Complex Cases (Stories 7-10)
- Multi-party transactions
- Blockchain queries
- Asset management
- System initialization

### Error Cases (Stories 11-15)
- Validation failures
- Transaction reverts
- Missing data scenarios
- Error handling

---

## Technical Notes

### Gas Optimization
- Contract deployment is cached to avoid redeployment
- Batch operations where possible (ERC721A for minting)

### Security Considerations
- Access control checks before operations
- Re-entrancy protection in smart contracts
- Input validation at multiple layers

### Performance Metrics
- Each operation tracks timing
- Gas costs are logged
- Database queries are optimized with indexes

### Watermarking Methods
- LSB (Least Significant Bit): Currently used
- SSL (Self-Supervised Learning): Available but optional
- Method selection via UI sidebar

