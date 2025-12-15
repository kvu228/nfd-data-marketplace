# Đóng Góp, Tính Mới và Khó Khăn - NFT-Based Data Marketplace

## 1. Đóng Góp Quan Trọng

### 1.1. Tích Hợp Blockchain với Watermarking Tự Động

**Đóng góp chính**: Hệ thống kết hợp công nghệ blockchain (NFT) với watermarking tự động để tạo ra một giải pháp truy vết tài sản số hoàn chỉnh và minh bạch.

- **Tự động hóa quy trình**: Watermark được tự động áp dụng trong quá trình giao dịch, không cần can thiệp thủ công
- **Bất biến trên blockchain**: Hash của tài sản có watermark được lưu trữ trên blockchain, đảm bảo tính không thể thay đổi
- **Truy vết kép**: Hỗ trợ cả watermark-based và hash-based traceability

### 1.2. Kiến Trúc Smart Contract Ba Tầng

**Đóng góp về kiến trúc**: Thiết kế hệ thống smart contract với Factory Pattern và phân tách trách nhiệm rõ ràng:

- **AssetAgreementFactory**: Quản lý việc tạo contracts cho các chủ sở hữu mới
- **AssetAgreement**: Mỗi chủ sở hữu có một contract riêng (one-to-many relationship)
- **AssetMarket**: Xử lý tập trung các giao dịch và phân phối royalty

**Lợi ích**:
- Tách biệt trách nhiệm giữa các contracts
- Dễ dàng mở rộng và bảo trì
- Tối ưu gas với ERC721A cho batch minting

### 1.3. Hệ Thống Truy Vết Kép (Dual Traceability)

**Đóng góp về khả năng truy vết**: Hệ thống cung cấp hai phương thức truy vết độc lập:

#### a) Watermark-based Traceability
- Extract watermark từ hình ảnh có watermark
- Map watermark IDs (owner_id, buyer_id) sang thông tin người dùng trong database
- Cho phép xác định người sở hữu và người mua từ hình ảnh bị rò rỉ

#### b) Hash-based Traceability
- Tính hash SHA256 của tài sản có watermark kết hợp với seller_id và buyer_id
- Lưu hash trên blockchain trong mapping `hashRecord`
- Truy vết giao dịch từ blockchain bằng hash
- Đảm bảo tính xác thực và không thể giả mạo

**Ưu điểm**:
- Redundancy: Nếu một phương thức thất bại, phương thức kia vẫn hoạt động
- Xác minh chéo: Có thể xác minh kết quả từ cả hai phương thức
- Phù hợp với các trường hợp khác nhau (có/không có hình ảnh gốc)

### 1.4. Hệ Thống Royalty Linh Hoạt

**Đóng góp về kinh tế**: Thiết kế hệ thống royalty phức tạp và công bằng:

- **Owner Royalty**: Chủ sở hữu gốc nhận phần trăm từ mọi giao dịch bán lại
- **Market Royalty**: Thị trường nhận phần trăm từ mọi giao dịch
- **Tự động phân phối**: Payment được phân phối tự động trong smart contract
- **Có thể cấu hình**: Cả owner và market có thể thay đổi royalty percentage

**Logic phân phối**:
```
Tổng tiền = msg.value
Market cut = msg.value * marketRoyalty / 1 ether
Remaining = msg.value - marketRoyalty

Nếu bán lần đầu (originalOwner == seller):
  → Original owner nhận: remaining

Nếu bán lại (originalOwner != seller):
  → Owner royalty = remaining * ownerRoyalty / 1 ether
  → Seller nhận: remaining - ownerRoyalty
```

### 1.5. Kiểm Soát Quyền Bán Lại (Resale Control)

**Đóng góp về quyền sở hữu**: Cho phép chủ sở hữu gốc kiểm soát quyền bán lại tài sản:

- **Resale Flag**: Mỗi NFT có cờ `resaleAllowed` được set khi mint
- **Chỉ chủ sở hữu gốc mới có thể thay đổi**: Đảm bảo quyền kiểm soát
- **Enforcement**: Không thể set `forSale = true` nếu `resaleAllowed = false`

**Ứng dụng**:
- Bảo vệ quyền của người tạo nội dung
- Kiểm soát phân phối tài sản số
- Hỗ trợ các mô hình kinh doanh khác nhau

### 1.6. Tối Ưu Gas với ERC721A

**Đóng góp về hiệu quả**: Sử dụng ERC721A thay vì ERC721 tiêu chuẩn:

- **Batch Minting**: Mint nhiều NFT trong một transaction
- **Gas Optimization**: Giảm đáng kể chi phí gas khi mint nhiều tài sản
- **Tương thích**: Vẫn tuân thủ các tiêu chuẩn NFT phổ biến

### 1.7. Hỗ Trợ Dual Watermarking

**Đóng góp về công nghệ watermarking**: Hệ thống hỗ trợ hai phương pháp watermarking:

- **LSB Watermarking**: Nhanh, đơn giản, phù hợp cho development
- **SSL Watermarking**: Robust, dựa trên deep learning, phù hợp cho production
- **Interface thống nhất**: Cả hai có cùng interface, dễ dàng thay đổi

---

## 2. Tính Mới (Novelty)

### 2.1. Tích Hợp Watermarking vào Quy Trình Giao Dịch Blockchain

**Tính mới**: Chưa có nhiều hệ thống tích hợp watermarking tự động vào quy trình giao dịch NFT:

- **Tự động hóa**: Watermark được tạo tự động khi mua, không cần bước riêng
- **Đồng bộ**: Hash của tài sản có watermark được cập nhật lên blockchain ngay sau khi watermark
- **Không thể tách rời**: Watermark và blockchain transaction được liên kết chặt chẽ

**Khác biệt với các hệ thống hiện có**:
- Hầu hết NFT marketplace không có watermarking tự động
- Các hệ thống watermarking thường độc lập với blockchain
- Chưa có tích hợp sâu giữa watermarking và smart contract

### 2.2. Hash-based Traceability trên Blockchain

**Tính mới**: Sử dụng hash của tài sản có watermark để truy vết trên blockchain:

- **Mapping Hash → Token ID**: Lưu trữ mapping `hashRecord[hash] = tokenId` trên blockchain
- **Truy vết ngược**: Từ hash có thể tìm được token ID và owner hiện tại
- **Xác minh tính xác thực**: Hash được tính từ tài sản + seller_id + buyer_id, đảm bảo tính duy nhất

**Ứng dụng mới**:
- Xác minh quyền sở hữu từ hình ảnh có watermark
- Truy vết lịch sử giao dịch không cần token ID
- Phát hiện tài sản bị rò rỉ và xác định nguồn gốc

### 2.3. One-to-Many Contract Architecture

**Tính mới**: Mỗi chủ sở hữu có một AssetAgreement contract riêng:

- **Isolation**: Tài sản của mỗi chủ sở hữu được quản lý độc lập
- **Customization**: Mỗi chủ sở hữu có thể set royalty riêng
- **Scalability**: Dễ dàng mở rộng mà không ảnh hưởng đến các chủ sở hữu khác

**Khác biệt**:
- Hầu hết NFT marketplace sử dụng một contract cho tất cả
- Kiến trúc này cho phép quản lý tốt hơn và linh hoạt hơn

### 2.4. Kết Hợp Watermarking với Metadata trên Blockchain

**Tính mới**: Metadata của NFT bao gồm cả hash của tài sản có watermark:

- **DataAsset Struct**: Bao gồm `assetHash` để lưu hash của tài sản có watermark
- **Cập nhật động**: Hash được cập nhật mỗi khi có giao dịch mới
- **Liên kết chặt chẽ**: Watermark và blockchain metadata không thể tách rời

### 2.5. Resale Control với Royalty System

**Tính mới**: Kết hợp kiểm soát quyền bán lại với hệ thống royalty:

- **Resale Flag**: Kiểm soát xem tài sản có thể bán lại hay không
- **Royalty cho chủ sở hữu gốc**: Ngay cả khi bán lại, chủ sở hữu gốc vẫn nhận royalty
- **Enforcement**: Smart contract đảm bảo các quy tắc được tuân thủ

---

## 3. Khó Khăn và Thách Thức

### 3.1. Đồng Bộ Giữa Off-chain và On-chain

**Khó khăn**: Watermarking được thực hiện off-chain nhưng hash phải được lưu on-chain:

**Giải pháp**:
- Tạo watermark trước khi gửi transaction
- Tính hash ngay sau khi watermark
- Gửi transaction `updateHash()` trước `purchase()`
- Sử dụng transaction receipt để đảm bảo thứ tự

**Thách thức**:
- Đảm bảo tính nhất quán giữa watermark và hash
- Xử lý trường hợp transaction thất bại
- Quản lý state trong quá trình giao dịch

### 3.2. Gas Optimization

**Khó khăn**: Chi phí gas trên Ethereum có thể rất cao:

**Giải pháp đã áp dụng**:
- Sử dụng ERC721A thay vì ERC721 cho batch minting
- Tối ưu cấu trúc dữ liệu trong smart contract
- Sử dụng mapping thay vì arrays khi có thể
- Giảm số lượng storage operations

**Thách thức còn lại**:
- Chi phí lưu trữ hash trên blockchain
- Chi phí cho mỗi giao dịch mua/bán
- Cần cân nhắc giữa tính năng và chi phí

### 3.3. Bảo Mật Smart Contract

**Khó khăn**: Smart contract phải an toàn trước các lỗ hổng phổ biến:

**Giải pháp đã áp dụng**:
- **Re-entrancy Protection**: Modifier `noReEntrancy` trong AssetMarket
- **Access Control**: Sử dụng OpenZeppelin AccessControl với roles
- **Input Validation**: Kiểm tra tất cả input trước khi xử lý
- **Ownership Verification**: Kiểm tra quyền sở hữu trước khi cho phép thao tác

**Thách thức**:
- Kiểm tra kỹ lưỡng logic phân phối payment
- Đảm bảo không có lỗ hổng trong access control
- Xử lý edge cases và các tình huống bất thường

### 3.4. Xử Lý Watermarking với Nhiều Loại File

**Khó khăn**: Watermarking hiện tại chỉ hỗ trợ hình ảnh:

**Giải pháp hiện tại**:
- Sử dụng LSB watermarking cho hình ảnh
- Hỗ trợ các format phổ biến (PNG, JPG)
- Xử lý với PIL/Pillow

**Thách thức**:
- Mở rộng hỗ trợ các loại file khác (video, audio, documents)
- Xử lý các file lớn
- Đảm bảo watermark không làm hỏng file gốc

### 3.5. Robustness của Watermark

**Khó khăn**: Watermark có thể bị mất hoặc hỏng khi file bị chỉnh sửa:

**Giải pháp**:
- **LSB Watermarking**: Đơn giản nhưng dễ bị mất khi nén hoặc chỉnh sửa
- **SSL Watermarking**: Robust hơn với deep learning nhưng phức tạp hơn

**Thách thức**:
- Cân nhắc giữa robustness và độ phức tạp
- Xử lý các trường hợp watermark bị hỏng
- Cải thiện khả năng chống lại các cuộc tấn công

### 3.6. Quản Lý State và Transaction Ordering

**Khó khăn**: Đảm bảo các transaction được thực hiện đúng thứ tự:

**Quy trình hiện tại**:
1. Tạo watermark
2. Tính hash
3. `updateHash()` transaction
4. `purchase()` transaction

**Thách thức**:
- Đảm bảo `updateHash()` hoàn thành trước `purchase()`
- Xử lý trường hợp một trong hai transaction thất bại
- Quản lý nonce và gas price

### 3.7. Scalability và Performance

**Khó khăn**: Hệ thống cần xử lý nhiều giao dịch đồng thời:

**Giải pháp hiện tại**:
- Sử dụng local node cho development
- SQLite database cho metadata
- Local file storage

**Thách thức**:
- Mở rộng lên mainnet/testnet
- Xử lý nhiều người dùng đồng thời
- Tối ưu performance của watermarking
- Cải thiện thời gian phản hồi

### 3.8. User Experience

**Khó khăn**: Người dùng cần hiểu và sử dụng hệ thống dễ dàng:

**Giải pháp**:
- Streamlit interface đơn giản
- Hướng dẫn rõ ràng cho từng bước
- Hiển thị log chi tiết

**Thách thức**:
- Giảm độ phức tạp của quy trình
- Cải thiện feedback cho người dùng
- Xử lý lỗi một cách thân thiện

### 3.9. Tích Hợp với Các Dịch Vụ Bên Ngoài

**Khó khăn**: Hệ thống cần tích hợp với các dịch vụ khác:

**Thách thức**:
- Tích hợp IPFS cho lưu trữ phi tập trung
- Tích hợp với các wallet (MetaMask, WalletConnect)
- Tích hợp với các oracle để lấy dữ liệu bên ngoài
- Hỗ trợ multi-chain

### 3.10. Testing và Verification

**Khó khăn**: Đảm bảo hệ thống hoạt động đúng trong mọi trường hợp:

**Thách thức**:
- Test smart contracts với nhiều scenarios
- Test tích hợp giữa watermarking và blockchain
- Test performance và scalability
- Security audit cho smart contracts

---

## 4. Kết Luận

### 4.1. Tóm Tắt Đóng Góp

Dự án đã đóng góp một giải pháp tích hợp blockchain và watermarking cho thị trường tài sản số, với các điểm nổi bật:

1. **Kiến trúc smart contract ba tầng** với Factory Pattern
2. **Hệ thống truy vết kép** (watermark + hash-based)
3. **Royalty system linh hoạt** và công bằng
4. **Resale control** cho chủ sở hữu gốc
5. **Tối ưu gas** với ERC721A
6. **Tích hợp tự động** watermarking vào quy trình giao dịch

### 4.2. Tính Mới

Các điểm mới của dự án:

1. Tích hợp watermarking tự động vào quy trình giao dịch blockchain
2. Hash-based traceability trên blockchain
3. One-to-many contract architecture
4. Kết hợp watermarking với metadata trên blockchain
5. Resale control với royalty system

### 4.3. Khó Khăn Đã Vượt Qua

Các khó khăn chính đã được giải quyết:

1. Đồng bộ off-chain và on-chain với transaction ordering
2. Gas optimization với ERC721A
3. Bảo mật smart contract với re-entrancy protection và access control
4. Xử lý watermarking với LSB và SSL
5. Quản lý state và transaction ordering

### 4.4. Hướng Phát Triển Tương Lai

1. **Mở rộng hỗ trợ file types**: Video, audio, documents
2. **Tích hợp IPFS**: Lưu trữ tài sản phi tập trung
3. **Multi-chain support**: Hỗ trợ nhiều blockchain
4. **Cải thiện robustness**: Nâng cấp watermarking
5. **Production-ready**: Chuyển từ local development sang production
6. **Security audit**: Audit toàn diện cho smart contracts
7. **Performance optimization**: Cải thiện tốc độ và scalability

---

## 5. Tài Liệu Tham Khảo

- OpenZeppelin Contracts: https://docs.openzeppelin.com/contracts
- ERC721A Specification: https://erc721a.org/
- SSL Watermarking Paper: https://arxiv.org/abs/2112.09581
- Hardhat Documentation: https://hardhat.org/docs
- Web3.py Documentation: https://web3py.readthedocs.io/


