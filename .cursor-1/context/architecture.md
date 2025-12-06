# Architecture - NFT-Based Data Marketplace

## Kiến Trúc Tổng Quan

Hệ thống tuân theo kiến trúc **ba tầng** (Three-Tier Architecture):

```
┌─────────────────────────────────────────┐
│      Tầng Presentation (Streamlit)      │
│   - User Interface                      │
│   - User Interaction                    │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    Tầng Business Logic (Python)         │
│   - Application Logic                   │
│   - Watermarking Processing             │
│   - Contract Interaction                │
└─────────────────────────────────────────┘
        │                    │
        ▼                    ▼
┌──────────────┐    ┌──────────────┐
│  Blockchain  │    │   Database   │
│ (Smart       │    │   (SQLite)   │
│  Contracts)  │    │              │
└──────────────┘    └──────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│  Dịch vụ Watermarking (Deep Learning)   │
│   - LSB Watermarking                    │
│   - SSL Watermarking (optional)         │
└─────────────────────────────────────────┘
```

## Các Thành Phần Chính

### 1. Presentation Layer (Frontend)

#### Streamlit Application (`src/app.py`)
- **Chức năng**: Entry point của ứng dụng
- **Trách nhiệm**:
  - Khởi tạo và quản lý các module
  - Deploy smart contracts (nếu chưa có)
  - Render UI với các tabs
- **Các Module**:
  - `UserRegistration`: Đăng ký người dùng
  - `Upload`: Upload và publish tài sản
  - `Market`: Giao dịch tài sản
  - `ExtractWatermark`: Truy vết và extract watermark
  - `Dashboard`: Xem và quản lý tài sản

### 2. Business Logic Layer

#### Contract Wrapper (`src/contract.py`)
- **Chức năng**: Wrapper Python cho smart contracts
- **Các Class**:
  - `Contract`: Base class cho tất cả contract wrappers
  - `AssetFactory`: Tương tác với AssetAgreementFactory
  - `AssetMarket`: Tương tác với AssetMarket contract
  - `AssetAgreement`: Tương tác với AssetAgreement contract
- **Tính năng**:
  - Deploy contracts (với caching)
  - Gửi transactions
  - Đọc state từ blockchain
  - Quản lý nonce và gas

#### Market Logic (`src/market.py`)
- **Chức năng**: Xử lý logic giao dịch
- **Quy trình mua hàng**:
  1. Lấy thông tin tài sản từ blockchain
  2. Tạo watermark với seller_id và buyer_id
  3. Tính hash của tài sản có watermark
  4. Update hash lên blockchain
  5. Thực hiện giao dịch mua

#### Upload Logic (`src/upload.py`)
- **Chức năng**: Xử lý upload và publish tài sản
- **Quy trình**:
  1. Lưu file vào local storage
  2. Tạo hoặc lấy AssetAgreement contract
  3. Mint NFT với metadata (price, resaleAllowed)
  4. Lưu thông tin vào database

#### Watermark Extraction (`src/extract_watermark.py`)
- **Chức năng**: Extract watermark và truy vết
- **Tính năng**:
  - Extract watermark từ hình ảnh
  - Map watermark IDs sang user names
  - Truy vết giao dịch từ hash

### 3. Blockchain Layer

#### Smart Contract Architecture

Hệ thống sử dụng **3 smart contracts chính**:

##### AssetAgreementFactory.sol
- **Mục đích**: Factory pattern để tạo AssetAgreement contracts
- **Chức năng**:
  - Tạo AssetAgreement contract mới cho mỗi chủ sở hữu
  - Emit event khi tạo contract mới
- **Pattern**: Factory Pattern

##### AssetAgreement.sol
- **Mục đích**: ERC721A contract quản lý NFT cho mỗi chủ sở hữu
- **Inheritance**: ERC721A, AccessControl
- **Roles**:
  - `OWNER_ROLE`: Chủ sở hữu gốc
  - `MARKET_ROLE`: Market contract
- **Data Structures**:
  - `DataAsset`: Metadata của mỗi NFT (price, hash, forSale, resaleAllowed)
  - `mintedAssets`: Mapping tokenID → DataAsset
  - `hashRecord`: Mapping hash → tokenID
- **Chức năng chính**:
  - Mint NFT
  - Quản lý metadata
  - Update hash (khi watermark)
  - Quản lý sale status
  - Royalty management

##### AssetMarket.sol
- **Mục đích**: Market contract xử lý giao dịch
- **Inheritance**: Ownable
- **Security**: Re-entrancy protection
- **Chức năng chính**:
  - Purchase asset
  - Process payment với royalty distribution
  - Update sale status
  - Update price
  - Update hash
  - Traceability: getAssetSaleRecord

#### Contract Interaction Flow

```
User → Python App → Web3.py → Ethereum Node → Smart Contracts
```

### 4. Database Layer

#### Schema (`src/db/schema.sql`)

**Table: users**
- `id`: Primary key
- `uname`: Tên người dùng
- `wallet`: Ethereum wallet address
- `agreement`: Address của AssetAgreement contract

**Table: assets**
- `id`: Primary key
- `owner_id`: Foreign key → users.id
- `filepath`: Đường dẫn file tài sản
- `token_id`: Token ID trên blockchain

#### Database Access (`src/db.py`)
- **Function**: `get_demo_db()` - Trả về SQLite connection

### 5. Watermarking Layer

#### LSB Watermarking (`src/lsb_watermarking/`)
- **Thuật toán**: Least Significant Bit steganography
- **Interface**:
  - `Watermark.set_watermark(owner_id, buyer_id)`: Set watermark message
  - `Watermark.watermark_image(img_path)`: Watermark image
  - `Watermark.extract_watermark(img_path)`: Extract watermark
- **Format**: 12 bits (6 bits owner_id + 6 bits buyer_id)
- **Modules**:
  - `encode.py`: Encoding logic
  - `decode.py`: Decoding logic
  - `utils.py`: Utility functions

#### SSL Watermarking (`src/ssl_watermarking/`)
- **Thuật toán**: Self-Supervised Learning watermarking
- **Status**: Có sẵn nhưng không được sử dụng trong code hiện tại
- **Interface**: Tương tự LSB watermarking

## Data Flow

### 1. User Registration Flow

```
User Input → UserRegistration.register_user()
  → Database INSERT
  → Success/Error Message
```

### 2. Asset Publishing Flow

```
User Upload File → Upload.render()
  → Save to local storage
  → Check/Create AssetAgreement contract
  → Mint NFT (AssetAgreement.mint())
  → Insert to database
  → Display success
```

### 3. Trading Flow

```
Buyer Selects Asset → Market.on_image_buy()
  → Get asset info from blockchain
  → Load original image
  → Create watermark (owner_id, buyer_id)
  → Compute hash (SHA256)
  → Update hash on blockchain
  → Execute purchase transaction
  → Transfer ownership
  → Distribute payment (royalty)
```

### 4. Traceability Flow

```
Upload Watermarked Image → ExtractWatermark.render_extract_watermark()
  → Extract watermark (owner_id, buyer_id)
  → Query database for user names
  → Display result
```

### 5. Hash-based Traceability Flow

```
Upload Original Image + IDs → ExtractWatermark.render_recovery()
  → Compute hash (SHA256 with IDs)
  → Query blockchain (getAssetSaleRecord)
  → Display transaction record
```

## Security Architecture

### Smart Contract Security

1. **Access Control**:
   - OpenZeppelin AccessControl cho role-based access
   - OWNER_ROLE và MARKET_ROLE phân tách rõ ràng

2. **Re-entrancy Protection**:
   - `noReEntrancy` modifier trong AssetMarket
   - Lock mechanism

3. **Ownership Verification**:
   - Kiểm tra `msg.sender == ownerOf(tokenId)` trước khi cho phép thao tác

4. **Input Validation**:
   - Kiểm tra giá trị royalty (0-1 ether)
   - Kiểm tra token existence
   - Kiểm tra sale status

### Application Security

1. **Transaction Signing**:
   - Private key management (có thể cải thiện)
   - Nonce management

2. **Data Validation**:
   - Kiểm tra user input
   - Validate wallet addresses

## Deployment Architecture

### Local Development

```
┌─────────────────┐
│  Streamlit App  │ (Port 8501)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Hardhat Node   │ (Port 8545)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │ (src/db/demo.db)
└─────────────────┘
```

### Contract Deployment

- **Deployment Strategy**: Deploy once, cache address
- **Storage**: Contract addresses lưu trong `contracts.json`
- **Decorator**: `@ContractDeployOnce` đảm bảo chỉ deploy một lần

## Scalability Considerations

### Current Limitations

1. **Storage**: Tài sản lưu trên local file system
2. **Database**: SQLite không phù hợp cho production
3. **Blockchain**: Local node, chưa support mainnet/testnet
4. **Watermarking**: Chỉ hỗ trợ hình ảnh

### Potential Improvements

1. **IPFS Integration**: Lưu trữ tài sản trên IPFS
2. **PostgreSQL/MySQL**: Database production-ready
3. **Multi-chain Support**: Hỗ trợ nhiều blockchain
4. **Batch Processing**: Xử lý watermarking hàng loạt
5. **Caching Layer**: Cache blockchain data
6. **API Layer**: REST/GraphQL API thay vì direct Streamlit

## Integration Points

### External Services

1. **Ethereum Node**: 
   - Local: Hardhat node
   - Remote: Có thể config Infura/Alchemy

2. **File Storage**:
   - Local: File system
   - Future: IPFS, AWS S3, etc.

### Internal Dependencies

1. **Web3.py ↔ Smart Contracts**: Contract interaction
2. **Python ↔ SQLite**: Database operations
3. **Watermarking ↔ Images**: Image processing
4. **Streamlit ↔ All**: UI orchestration

