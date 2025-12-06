# Context - NFT-Based Data Marketplace

## Tổng Quan Dự Án

**NFT-Based Data Marketplace** là một thị trường phi tập trung (decentralized marketplace) cho phép giao dịch tài sản số dưới dạng NFT với công nghệ watermarking tích hợp để truy vết và xác minh quyền sở hữu.

### Mục Đích

Dự án này là một proof-of-concept cho thị trường trao đổi dữ liệu dựa trên NFT, cho phép:

- **Chủ sở hữu dữ liệu** xuất bản và bán tài sản số (hình ảnh, tệp tin) dưới dạng NFT
- **Người mua** mua tài sản từ thị trường
- **Watermarking tự động** được áp dụng trong quá trình giao dịch để đảm bảo khả năng truy vết
- **Tính năng truy vết** để theo dõi nguồn gốc tài sản và lịch sử giao dịch

### Công Nghệ Sử Dụng

#### Backend & Blockchain
- **Solidity**: Smart contracts cho Ethereum blockchain
- **Hardhat**: Framework phát triển và testing smart contracts
- **Web3.py**: Thư viện Python để tương tác với Ethereum blockchain
- **OpenZeppelin**: Thư viện smart contract bảo mật (ERC721, AccessControl)
- **ERC721A**: Standard NFT với gas optimization

#### Frontend
- **Streamlit**: Framework Python để xây dựng web application
- **PIL/Pillow**: Xử lý hình ảnh

#### Watermarking
- **LSB Watermarking**: Least Significant Bit steganography (hiện tại đang sử dụng)
- **SSL Watermarking**: Self-Supervised Learning watermarking (có sẵn nhưng không được sử dụng)

#### Database
- **SQLite**: Cơ sở dữ liệu quan hệ để lưu trữ thông tin người dùng và tài sản

#### Development Tools
- **Poetry**: Quản lý dependencies Python
- **npm**: Quản lý packages Node.js
- **Python 3.8.15**: Phiên bản Python được chỉ định

### Đối Tượng Sử Dụng

1. **Data Owners (Chủ sở hữu dữ liệu)**: Người tạo và xuất bản tài sản số
2. **Buyers (Người mua)**: Người mua tài sản từ thị trường
3. **Marketplace Operators**: Người vận hành thị trường

### Tính Năng Chính

1. **User Registration**: Đăng ký người dùng với wallet address
2. **Asset Publishing**: Xuất bản tài sản dưới dạng NFT với giá và quyền bán lại
3. **Trading**: Mua/bán tài sản trên thị trường
4. **Watermarking**: Tự động watermark tài sản khi giao dịch
5. **Traceability**: Truy vết quyền sở hữu và lịch sử giao dịch
6. **Dashboard**: Xem và quản lý tài sản đã mua

### Môi Trường Phát Triển

- **Local Ethereum Node**: Hardhat local node tại `http://127.0.0.1:8545/`
- **Development Database**: SQLite tại `src/db/demo.db`
- **Asset Storage**: Local file system tại thư mục `images/`

### Cấu Trúc Dự Án

```
nfd-data-marketplace/
├── contracts/              # Smart contracts Solidity
│   ├── AssetAgreementFactory.sol
│   ├── AssetAgreement.sol
│   ├── AssetMarket.sol
│   └── IAssetAgreement.sol
├── src/                    # Mã nguồn Python
│   ├── app.py             # Ứng dụng Streamlit chính
│   ├── contract.py        # Wrapper smart contract
│   ├── dashboard.py       # Module dashboard
│   ├── market.py          # Logic thị trường
│   ├── upload.py          # Chức năng upload tài sản
│   ├── user_registration.py
│   ├── extract_watermark.py
│   ├── db/                # Database schema và seed data
│   ├── lsb_watermarking/  # LSB watermarking implementation
│   └── ssl_watermarking/  # SSL watermarking implementation
├── artifacts/             # Compiled smart contracts
├── images/               # Stored assets
└── .cursor/context/      # Documentation (này)
```

### Workflow Tổng Quan

1. **Registration**: Người dùng đăng ký với tên và wallet address
2. **Publishing**: Chủ sở hữu upload tài sản, đặt giá, mint NFT
3. **Trading**: Người mua chọn và mua tài sản
4. **Watermarking**: Hệ thống tự động watermark tài sản với owner_id và buyer_id
5. **Blockchain Update**: Hash của tài sản có watermark được lưu trên blockchain
6. **Traceability**: Có thể truy vết quyền sở hữu từ watermark hoặc hash

### Điểm Đặc Biệt

- **Dual Watermarking Support**: Hỗ trợ cả LSB và SSL watermarking
- **Royalty System**: Hệ thống phí bản quyền cho chủ sở hữu gốc và thị trường
- **Resale Control**: Kiểm soát quyền bán lại tài sản
- **Hash-based Traceability**: Truy vết dựa trên hash của tài sản có watermark
- **One-to-Many Relationship**: Mỗi chủ sở hữu có một AssetAgreement contract riêng

### Security Considerations

- **Access Control**: Sử dụng OpenZeppelin AccessControl cho phân quyền
- **Re-entrancy Protection**: Modifier `noReEntrancy` trong AssetMarket
- **Ownership Verification**: Kiểm tra quyền sở hữu trước khi cho phép thao tác
- **Hash Verification**: Xác minh hash khi truy vết tài sản

### Limitations & Future Work

- Hiện tại chỉ hỗ trợ local development
- Chưa có tích hợp IPFS cho lưu trữ tài sản phi tập trung
- Watermarking chỉ hỗ trợ hình ảnh
- Chưa có authentication/authorization cho web interface
- Chưa có test coverage đầy đủ

