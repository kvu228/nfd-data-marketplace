#!/usr/bin/env python3
"""
Script để test kết nối với Hardhat node và kiểm tra events
"""
from web3 import Web3
import json

# Kết nối với Hardhat node
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545/"))

print("=" * 50)
print("KIỂM TRA HARDHAT NODE")
print("=" * 50)

# 1. Kiểm tra kết nối
print("\n1. Kiểm tra kết nối:")
if w3.isConnected():
    print("✅ Kết nối thành công với Hardhat node")
    print(f"   Chain ID: {w3.eth.chain_id}")
    print(f"   Block number: {w3.eth.block_number}")
else:
    print("❌ Không thể kết nối với Hardhat node")
    exit(1)

# 2. Kiểm tra accounts
print("\n2. Kiểm tra accounts:")
try:
    accounts = w3.eth.accounts
    print(f"✅ Tìm thấy {len(accounts)} accounts:")
    for i, account in enumerate(accounts[:5]):  # Chỉ hiển thị 5 accounts đầu
        balance = w3.eth.get_balance(account)
        print(f"   Account {i}: {account}")
        print(f"   Balance: {w3.fromWei(balance, 'ether')} ETH")
except Exception as e:
    print(f"❌ Lỗi khi lấy accounts: {e}")

# 3. Kiểm tra transaction gần nhất
print("\n3. Kiểm tra transaction gần nhất:")
try:
    latest_block = w3.eth.get_block('latest', full_transactions=True)
    print(f"   Block number: {latest_block.number}")
    print(f"   Transactions: {len(latest_block.transactions)}")
    
    if len(latest_block.transactions) > 0:
        tx = latest_block.transactions[-1]
        print(f"   Latest transaction hash: {tx.hash.hex()}")
        
        # Lấy receipt
        receipt = w3.eth.get_transaction_receipt(tx.hash)
        print(f"   Status: {'✅ Success' if receipt.status == 1 else '❌ Failed'}")
        print(f"   Logs: {len(receipt.logs)}")
        
        if len(receipt.logs) > 0:
            print("   Events:")
            for i, log in enumerate(receipt.logs):
                print(f"      Log {i}: Address={log.address}, Topics={len(log.topics)}")
        else:
            print("   ⚠️  Không có logs trong transaction này")
except Exception as e:
    print(f"❌ Lỗi khi lấy block: {e}")

# 4. Test deploy một contract đơn giản (nếu có factory)
print("\n4. Test event emission:")
print("   (Cần chạy transaction trong app để test)")

print("\n" + "=" * 50)
print("KẾT QUẢ KIỂM TRA")
print("=" * 50)
print("\n💡 Để xem logs chi tiết của Hardhat node:")
print("   - Xem terminal nơi Hardhat node đang chạy (s044)")
print("   - Hoặc restart Hardhat node với: npx hardhat node")
print("\n💡 Nếu transaction không có logs:")
print("   - Có thể Hardhat không lưu logs cho internal contract creation")
print("   - Thử restart Hardhat node")
print("   - Kiểm tra xem contract có được compile đúng không")

