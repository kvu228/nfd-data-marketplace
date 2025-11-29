# NFT-Based Data Marketplace

Một thị trường phi tập trung để giao dịch tài sản số dưới dạng NFT với công nghệ watermarking tích hợp để truy vết và xác minh quyền sở hữu.

## Tổng Quan

Dự án này là một proof-of-concept cho thị trường trao đổi dữ liệu dựa trên NFT, cho phép:

- **Chủ sở hữu dữ liệu** xuất bản và bán tài sản số (hình ảnh, tệp tin) dưới dạng NFT
- **Người mua** mua tài sản từ thị trường
- **Watermarking tự động** được áp dụng trong quá trình giao dịch để đảm bảo khả năng truy vết
- **Tính năng truy vết** để theo dõi nguồn gốc tài sản và lịch sử giao dịch

Hệ thống kết hợp công nghệ blockchain (smart contract Ethereum) với watermarking dựa trên deep learning để tạo ra một thị trường an toàn, có thể truy vết cho tài sản số.

## Tính Năng

- **Tích hợp Smart Contract**: Kiến trúc smart contract ba tầng để quản lý tài sản an toàn
- **Hỗ trợ Watermarking kép**: 
  - SSL Watermarking (Watermarking deep learning dựa trên Self-Supervised Learning)
  - LSB Watermarking (Steganography Least Significant Bit)
- **Giao diện Web**: Dashboard dựa trên Streamlit cho tương tác người dùng
- **Truy vết**: Theo dõi quyền sở hữu tài sản và lịch sử giao dịch thông qua trích xuất watermark
- **Hệ thống Royalty**: Phí bản quyền tích hợp cho người tạo tài sản
- **Phát triển Local**: Hỗ trợ đầy đủ node Ethereum local thông qua Hardhat

## Kiến Trúc

Hệ thống tuân theo kiến trúc ba tầng:

```
┌─────────────────────────────────────────┐
│      Tầng Frontend (Streamlit)          │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    Tầng Business Logic (Python)         │
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
└─────────────────────────────────────────┘
```

## Thiết Kế Smart Contract

Thị trường sử dụng ba smart contract chính:

### 1. AssetAgreementFactory.sol
- **Mục đích**: Factory contract để tạo các Asset Agreement contracts
- **Chức năng**: Hoạt động như một hệ thống đăng ký chủ sở hữu
- **Tính năng chính**:
  - Cho phép chủ sở hữu dữ liệu mới đăng ký trên thị trường
  - Triển khai một contract `AssetAgreement` mới cho mỗi chủ sở hữu
  - Liên kết mỗi contract với địa chỉ ví của chủ sở hữu

### 2. AssetAgreement.sol
- **Mục đích**: Contract ERC721A quản lý tài sản NFT cho mỗi chủ sở hữu
- **Chức năng**: Tạo mối quan hệ một-nhiều giữa chủ sở hữu và người mua
- **Tính năng chính**:
  - Mint tài sản mới để bán
  - Quản lý metadata tài sản (giá, hash, trạng thái bán)
  - Quản lý quyền sở hữu
  - Quản lý phí bản quyền
  - Ánh xạ hash của hình ảnh có watermark với token ID

### 3. AssetMarket.sol
- **Mục đích**: Contract thị trường xử lý các giao dịch mua hàng
- **Chức năng**: Giao diện chính cho người mua để mua tài sản
- **Tính năng chính**:
  - Xử lý giao dịch mua hàng
  - Xác thực mua hàng với contract Asset Agreement của chủ sở hữu
  - Chuyển quyền sở hữu tài sản
  - Phân phối thanh toán (phí bản quyền cho chủ sở hữu và thị trường)
  - Theo dõi hồ sơ bán tài sản

### Timeline Smart Contract

Biểu đồ sau minh họa luồng sự kiện từ góc độ smart contract:

![](assets/smartcontract_timeline.png)

## Yêu Cầu Hệ Thống

Trước khi thiết lập dự án, đảm bảo bạn đã cài đặt các phần mềm sau:

- **Python**: 3.8.15 (theo chỉ định trong `pyproject.toml`)
- **Node.js**: v16.14.0 (bắt buộc cho Hardhat)
- **Poetry**: Để quản lý phụ thuộc Python
- **npm**: Để quản lý gói Node.js
- **Conda**: Để quản lý môi trường (tùy chọn, nhưng được khuyến nghị)
- **SQLite3**: Để thao tác cơ sở dữ liệu
- **Git**: Để quản lý phiên bản

## Cài Đặt

### 1. Clone Repository

```bash
git clone <repository-url>
cd demo
```

### 2. Thiết Lập Môi Trường Python

Cài đặt các phụ thuộc bằng Poetry:

```bash
poetry install
```

Hoặc nếu sử dụng Conda:

```bash
conda create -n nft-data python=3.8.15
conda activate nft-data
pip install -r requirements.txt
```

### 3. Cài Đặt Phụ Thuộc Node.js

Đảm bảo bạn đang sử dụng Node.js v16.14.0, sau đó cài đặt các phụ thuộc:

```bash
npm install
```

### 4. Thiết Lập Mô Hình Watermarking

Tải xuống và đặt các tệp mô hình ML cần thiết:

#### Cho SSL Watermarking:

**Đặt trong `~/.cache/torch/hub/checkpoints`:**
- ResNet50: [Tải xuống](https://download.pytorch.org/models/resnet50-0676ba61.pth)

**Đặt trong `src/ssl_watermarking/models`:**
- DINO Trained ResNet50: [Tải xuống](https://dl.fbaipublicfiles.com/ssl_watermarking/dino_r50_plus.pth)

**Đặt trong `src/ssl_watermarking/normlayers`:**
- Normalization Layer: [Tải xuống](https://dl.fbaipublicfiles.com/ssl_watermarking/out2048_yfcc_orig.pth)

> **Lưu ý**: Các script bootstrap cho SSL watermarking (`bootstrap_ssl.sh` và `bootstrap_ssl.bat`) có thể tự động tải xuống các tệp này nếu chúng bị thiếu.

## Chạy Ứng Dụng

### Khởi Động Nhanh

Cách dễ nhất để chạy ứng dụng là sử dụng các script bootstrap, chúng sẽ xử lý:
- Biên dịch smart contract
- Khởi tạo cơ sở dữ liệu
- Khởi động node Ethereum
- Khởi chạy ứng dụng

#### Cho SSL Watermarking (Windows):

```bash
bootstrap_ssl.bat
```

#### Cho SSL Watermarking (Linux/Mac):

```bash
chmod +x bootstrap_ssl.sh
./bootstrap_ssl.sh
```

#### Cho LSB Watermarking (Windows):

```bash
bootstrap_lsb.bat
```

#### Cho LSB Watermarking (Linux/Mac):

```bash
chmod +x bootstrap_lsb.sh
./bootstrap_lsb.sh
```

### Thiết Lập Thủ Công

Nếu bạn muốn chạy các thành phần thủ công:

1. **Biên dịch Smart Contracts:**
   ```bash
   npx hardhat compile
   ```

2. **Khởi tạo Cơ sở Dữ liệu:**
   ```bash
   sqlite3 src/db/demo.db < src/db/schema.sql
   sqlite3 src/db/demo.db < src/db/seed.sql
   ```

3. **Khởi động Node Ethereum:**
   ```bash
   npx hardhat node
   ```
   Giữ terminal này mở. Node sẽ chạy trên `http://127.0.0.1:8545/`

4. **Khởi chạy Ứng dụng Streamlit:**
   ```bash
   streamlit run src/app.py
   ```

5. **Truy cập Ứng dụng:**
   Mở URL hiển thị trong terminal (thường là `http://localhost:8501`)

## Cấu Trúc Dự Án

```
.
├── archived/              # Mã nguồn đã lưu trữ/legacy
├── assets/                # Tài nguyên tài liệu
│   └── smartcontract_timeline.png
├── contracts/             # Smart contracts Solidity
│   ├── AssetAgreementFactory.sol
│   ├── AssetAgreement.sol
│   ├── AssetMarket.sol
│   └── IAssetAgreement.sol
|
├── src/                   # Mã nguồn Python
│   ├── app.py            # Ứng dụng Streamlit chính
│   ├── contract.py       # Wrapper smart contract
│   ├── dashboard.py      # Module dashboard
│   ├── db/               # Tệp và schema cơ sở dữ liệu
│   ├── lsb_watermarking/ # Triển khai LSB watermarking
│   ├── ssl_watermarking/ # Triển khai SSL watermarking
│   ├── market.py         # Logic thị trường
│   ├── upload.py         # Chức năng upload tài sản
│   └── user_registration.py
├── bootstrap_ssl.bat     # Bootstrap Windows cho SSL
├── bootstrap_ssl.sh     # Bootstrap Linux/Mac cho SSL
├── bootstrap_lsb.bat     # Bootstrap Windows cho LSB
├── bootstrap_lsb.sh     # Bootstrap Linux/Mac cho LSB
├── hardhat.config.js     # Cấu hình Hardhat
├── package.json          # Phụ thuộc Node.js
├── pyproject.toml        # Cấu hình Poetry
└── requirements.txt      # Phụ thuộc Python
```

## Endpoint Node Ethereum

### Phát Triển Local

Ứng dụng sử dụng node Hardhat local theo mặc định:

```
LOCAL_ETH_ENDPOINT = "http://127.0.0.1:8545/"
```

Các script bootstrap tự động khởi động node Hardhat cho bạn. Để thiết lập thủ công, chạy:

```bash
npx hardhat node
```

### Cấu Hình Testnet

> **⚠️ Cảnh báo Bảo mật**: Các endpoint và private key sau chỉ dành cho mục đích kiểm thử. Không sử dụng trong môi trường production hoặc với tiền thật.

Để kiểm thử trên testnet (Goerli), các endpoint sau có sẵn:

**Infura Goerli Endpoint:**
```
INFURA_GOERLI_ENDPOINT = "https://goerli.infura.io/v3/1f6bc018b78440dba6b8b0cafc36e912"
```

**Alchemy Goerli Endpoint:**
```
ALCHEMY_GOERLI_ENDPOINT = "https://eth-goerli.g.alchemy.com/v2/fTYyXArUCpY8yDBdvMgi9CTtQHNQdvjC"
```

> **Lưu ý**: Các cấu hình testnet này chỉ được sử dụng trong các công cụ CLI để đo hiệu suất. Ứng dụng demo hoạt động hoàn toàn với node Ethereum local.

## Hướng Dẫn Sử Dụng

### Đăng Ký Người Dùng

1. Điều hướng đến tab "User Registration"
2. Nhập tên và địa chỉ ví của bạn
3. Nhấp "Register" để tạo tài khoản

### Xuất Bản Tài Sản

1. Đi đến tab "Publish Asset"
2. Chọn tài khoản chủ sở hữu của bạn
3. Tải lên một tệp (hình ảnh hoặc tài sản số khác)
4. Đặt giá bằng ETH
5. Chọn có cho phép bán lại hay không
6. Nhấp "Publish" để mint tài sản dưới dạng NFT

### Giao Dịch Tài Sản

1. Điều hướng đến tab "Trade"
2. Duyệt các tài sản có sẵn
3. Chọn một tài sản để mua
4. Hoàn tất giao dịch

### Truy Vết

1. Đi đến tab "Identifiability/Traceability"
2. Tải lên một tài sản có watermark
3. Trích xuất watermark để xem lịch sử giao dịch và chuỗi quyền sở hữu

## Tài Liệu

Tài liệu chi tiết bổ sung có sẵn trong thư mục `doc/`:

- **[Tài liệu Kiến trúc](./doc/architecture.md)**: Kiến trúc hệ thống chi tiết
- **[Tài liệu Luồng Code](./doc/code-flow.md)**: Giải thích chi tiết về luồng code
- **[Tài liệu Components](./doc/components.md)**: Tài liệu cấp độ component

## Phát Triển

### Phát Triển Smart Contract

Smart contracts được viết bằng Solidity và biên dịch bằng Hardhat:

```bash
# Biên dịch contracts
npx hardhat compile

# Chạy tests (nếu có)
npx hardhat test

# Triển khai lên mạng local
npx hardhat run scripts/deploy.js --network localhost
```

### Phát Triển Python

Codebase Python sử dụng Poetry để quản lý phụ thuộc. Để thêm phụ thuộc mới:

```bash
poetry add <package-name>
```

## Khắc Phục Sự Cố

### Các Vấn Đề Thường Gặp

1. **Phiên bản Node.js không khớp**: Đảm bảo bạn đang sử dụng Node.js v16.14.0
   ```bash
   node --version  # Nên hiển thị v16.14.0
   ```

2. **Thiếu Mô hình ML**: Đảm bảo tất cả các tệp mô hình watermarking đã được tải xuống và đặt trong các thư mục đúng (xem bước Cài đặt 4)

3. **Cổng Đã Được Sử Dụng**: Nếu cổng 8545 (Hardhat) hoặc 8501 (Streamlit) đang được sử dụng, dừng quy trình xung đột hoặc thay đổi cổng trong cấu hình

4. **Lỗi Cơ sở Dữ liệu**: Nếu gặp lỗi cơ sở dữ liệu, thử reset cơ sở dữ liệu:
   ```bash
   rm src/db/demo.db
   sqlite3 src/db/demo.db < src/db/schema.sql
   sqlite3 src/db/demo.db < src/db/seed.sql
   ```

## Giấy Phép

Xem giấy phép của từng component riêng lẻ. Component SSL watermarking có tệp LICENSE riêng trong `src/ssl_watermarking/LICENSE`.

## Đóng Góp

Đây là một dự án proof-of-concept. Để đóng góp, vui lòng tuân theo các thực hành phát triển tiêu chuẩn và đảm bảo tất cả các test đều pass.

## Lời Cảm Ơn

- Triển khai SSL Watermarking dựa trên nghiên cứu từ Facebook AI Research
- Smart contracts sử dụng thư viện OpenZeppelin và ERC721A
- Được xây dựng với Streamlit, Hardhat và Web3.py

---