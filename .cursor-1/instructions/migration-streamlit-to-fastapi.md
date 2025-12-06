# Migration Guide: Streamlit → FastAPI + Frontend

## Tổng Quan

Hướng dẫn này mô tả cách chuyển đổi ứng dụng NFT Data Marketplace từ kiến trúc Streamlit monolith sang kiến trúc tách biệt Frontend/Backend với FastAPI.

### Kiến Trúc Hiện Tại (Streamlit)

```
┌─────────────────────────────────┐
│     Streamlit Application       │
│  (UI + Business Logic + API)    │
└─────────────────────────────────┘
```

### Kiến Trúc Mới (FastAPI + Frontend)

```
┌──────────────────┐         ┌──────────────────┐
│   Frontend       │  HTTP   │   FastAPI         │
│   (React/Vue)    │ ◄─────► │   Backend         │
└──────────────────┘         └──────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  Smart Contracts │
                            │  Database        │
                            │  Watermarking    │
                            └──────────────────┘
```

## Lợi Ích Của Migration

1. **Tách biệt concerns**: Frontend và Backend độc lập
2. **Scalability**: Dễ scale từng phần riêng biệt
3. **Flexibility**: Frontend có thể là web, mobile, hoặc desktop app
4. **Performance**: API có thể được cache và optimize
5. **Team collaboration**: Frontend và Backend teams làm việc độc lập
6. **Modern stack**: Sử dụng công nghệ hiện đại hơn

## Yêu Cầu

- Python 3.8.15+
- FastAPI
- Uvicorn (ASGI server)
- Python-multipart (cho file uploads)
- CORS middleware
- Frontend framework (React, Vue, hoặc vanilla JS)

## Bước 1: Cài Đặt Dependencies

### Thêm vào `pyproject.toml` hoặc `requirements.txt`

```toml
[tool.poetry.dependencies]
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
python-multipart = "^0.0.6"
pydantic = "^2.0.0"
```

Hoặc:

```txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.0.0
```

### Cài đặt

```bash
poetry add fastapi uvicorn[standard] python-multipart pydantic
# hoặc
pip install fastapi uvicorn[standard] python-multipart pydantic
```

## Bước 2: Tạo Cấu Trúc Thư Mục Mới

```
nfd-data-marketplace/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Configuration
│   │   ├── models/            # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── asset.py
│   │   │   └── transaction.py
│   │   ├── api/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── users.py
│   │   │   ├── assets.py
│   │   │   ├── market.py
│   │   │   ├── watermark.py
│   │   │   └── dashboard.py
│   │   ├── services/          # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   ├── asset_service.py
│   │   │   ├── market_service.py
│   │   │   └── watermark_service.py
│   │   └── utils/             # Utilities
│   │       ├── __init__.py
│   │       └── web3_utils.py
│   ├── requirements.txt
│   └── .env                   # Environment variables
├── frontend/                   # Frontend application
│   ├── src/
│   ├── public/
│   └── package.json
└── src/                        # Shared/legacy code
    ├── contract.py            # Keep as is
    ├── db.py                  # Keep as is
    ├── constants.py           # Keep as is
    └── ...
```

## Bước 3: Tạo FastAPI Application

### `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import users, assets, market, watermark, dashboard
from app.config import settings

app = FastAPI(
    title="NFT Data Marketplace API",
    description="API for NFT-based data marketplace with watermarking",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for uploaded images)
app.mount("/static", StaticFiles(directory="images"), name="static")

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(watermark.router, prefix="/api/watermark", tags=["watermark"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "NFT Data Marketplace API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Ethereum
    ETH_ENDPOINT: str = "http://127.0.0.1:8545/"
    MARKET_CONTRACT_ADDRESS: str = None
    FACTORY_CONTRACT_ADDRESS: str = None
    
    # Database
    DATABASE_PATH: str = "src/db/demo.db"
    
    # File Storage
    IMAGES_DIR: str = "images"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    # API
    API_V1_PREFIX: str = "/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Bước 4: Tạo Pydantic Models

### `backend/app/models/user.py`

```python
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    uname: str
    wallet: str

class UserResponse(BaseModel):
    id: int
    uname: str
    wallet: str
    agreement: Optional[str] = None

    class Config:
        from_attributes = True
```

### `backend/app/models/asset.py`

```python
from pydantic import BaseModel
from typing import Optional

class AssetCreate(BaseModel):
    owner_id: int
    price: float
    resale_allowed: bool

class AssetResponse(BaseModel):
    id: int
    owner_id: int
    filepath: str
    token_id: int
    price: float
    for_sale: bool
    resale_allowed: bool
    owner_name: str
    agreement_address: str

    class Config:
        from_attributes = True

class AssetMetadata(BaseModel):
    price: float
    asset_hash: Optional[str]
    for_sale: bool
    resale_allowed: bool
```

### `backend/app/models/transaction.py`

```python
from pydantic import BaseModel

class PurchaseRequest(BaseModel):
    agreement_address: str
    token_id: int
    buyer_id: int

class PurchaseResponse(BaseModel):
    transaction_hash: str
    watermarked_file_url: str
    asset_hash: str
    message: str
```

## Bước 5: Tạo API Routes

### `backend/app/api/users.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.utils.web3_utils import get_web3_provider

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    service = UserService()
    try:
        result = service.register_user(user.uname, user.wallet)
        if not result:
            raise HTTPException(status_code=400, detail="User already exists")
        return service.get_user_by_wallet(user.wallet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[UserResponse])
async def get_all_users():
    """Get all registered users"""
    service = UserService()
    return service.get_all_users()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID"""
    service = UserService()
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### `backend/app/api/assets.py`

```python
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from app.models.asset import AssetCreate, AssetResponse, AssetMetadata
from app.services.asset_service import AssetService

router = APIRouter()

@router.post("/publish", response_model=AssetResponse)
async def publish_asset(
    owner_id: int = Form(...),
    price: float = Form(...),
    resale_allowed: bool = Form(...),
    file: UploadFile = File(...)
):
    """Publish a new asset"""
    service = AssetService()
    try:
        result = service.publish_asset(
            owner_id=owner_id,
            file=file,
            price=price,
            resale_allowed=resale_allowed
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[AssetResponse])
async def get_all_assets():
    """Get all assets"""
    service = AssetService()
    return service.get_all_assets()

@router.get("/{token_id}", response_model=AssetMetadata)
async def get_asset_metadata(agreement_address: str, token_id: int):
    """Get asset metadata from blockchain"""
    service = AssetService()
    try:
        return service.get_asset_metadata(agreement_address, token_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/for-sale", response_model=List[AssetResponse])
async def get_assets_for_sale():
    """Get all assets available for sale"""
    service = AssetService()
    return service.get_assets_for_sale()
```

### `backend/app/api/market.py`

```python
from fastapi import APIRouter, HTTPException
from app.models.transaction import PurchaseRequest, PurchaseResponse
from app.services.market_service import MarketService

router = APIRouter()

@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_asset(request: PurchaseRequest):
    """Purchase an asset"""
    service = MarketService()
    try:
        result = service.purchase_asset(
            agreement_address=request.agreement_address,
            token_id=request.token_id,
            buyer_id=request.buyer_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets")
async def get_marketplace_assets():
    """Get all assets available in marketplace"""
    service = MarketService()
    return service.get_marketplace_assets()
```

### `backend/app/api/watermark.py`

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.services.watermark_service import WatermarkService

router = APIRouter()

@router.post("/extract")
async def extract_watermark(file: UploadFile = File(...)):
    """Extract watermark from image"""
    service = WatermarkService()
    try:
        result = service.extract_watermark(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trace")
async def trace_asset(
    original_owner: str,
    seller: str,
    buyer: str,
    file: UploadFile = File(...)
):
    """Trace asset using hash"""
    service = WatermarkService()
    try:
        result = service.trace_asset(
            original_owner=original_owner,
            seller=seller,
            buyer=buyer,
            file=file
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### `backend/app/api/dashboard.py`

```python
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.asset import AssetResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/assets/{user_id}", response_model=List[AssetResponse])
async def get_user_assets(user_id: int):
    """Get all assets owned by a user"""
    service = DashboardService()
    try:
        return service.get_user_assets(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/assets/{token_id}/sale-status")
async def update_sale_status(
    agreement_address: str,
    token_id: int,
    for_sale: bool,
    user_wallet: str
):
    """Update sale status of an asset"""
    service = DashboardService()
    try:
        return service.update_sale_status(
            agreement_address=agreement_address,
            token_id=token_id,
            for_sale=for_sale,
            user_wallet=user_wallet
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Bước 6: Tạo Services (Business Logic)

### `backend/app/services/user_service.py`

```python
from app.db import get_demo_db
from app.models.user import UserResponse
from typing import List, Optional

class UserService:
    def register_user(self, uname: str, wallet: str) -> bool:
        """Register a new user - migrated from UserRegistration.register_user()"""
        con = get_demo_db()
        try:
            res = con.execute(
                "SELECT COUNT(*) FROM users WHERE uname = ? OR wallet = ?",
                [uname, wallet]
            )
            n, = res.fetchone()
            
            if n > 0:
                return False
            
            con.execute(
                "INSERT INTO users (uname, wallet) VALUES (?, ?)",
                [uname, wallet]
            )
            con.commit()
            return True
        finally:
            con.close()
    
    def get_all_users(self) -> List[UserResponse]:
        """Get all users"""
        con = get_demo_db()
        try:
            res = con.execute("SELECT id, uname, wallet, agreement FROM users")
            users = []
            for row in res.fetchall():
                users.append(UserResponse(
                    id=row[0],
                    uname=row[1],
                    wallet=row[2],
                    agreement=row[3]
                ))
            return users
        finally:
            con.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID"""
        con = get_demo_db()
        try:
            res = con.execute(
                "SELECT id, uname, wallet, agreement FROM users WHERE id = ?",
                [user_id]
            )
            row = res.fetchone()
            if row:
                return UserResponse(
                    id=row[0],
                    uname=row[1],
                    wallet=row[2],
                    agreement=row[3]
                )
            return None
        finally:
            con.close()
    
    def get_user_by_wallet(self, wallet: str) -> Optional[UserResponse]:
        """Get user by wallet address"""
        con = get_demo_db()
        try:
            res = con.execute(
                "SELECT id, uname, wallet, agreement FROM users WHERE wallet = ?",
                [wallet]
            )
            row = res.fetchone()
            if row:
                return UserResponse(
                    id=row[0],
                    uname=row[1],
                    wallet=row[2],
                    agreement=row[3]
                )
            return None
        finally:
            con.close()
```

### `backend/app/services/asset_service.py`

```python
from app.db import get_demo_db
from app.models.asset import AssetResponse, AssetMetadata
from app.contract import AssetAgreement, AssetFactory
from app.constants import LOCAL_ENDPOINT
from app.config import settings
from os.path import basename, join
from uuid import uuid4
from typing import List
import shutil

class AssetService:
    def publish_asset(
        self,
        owner_id: int,
        file,
        price: float,
        resale_allowed: bool
    ) -> AssetResponse:
        """Publish asset - migrated from Upload.render()"""
        con = get_demo_db()
        try:
            # Get owner info
            res = con.execute(
                "SELECT id, wallet, agreement FROM users WHERE id = ?",
                [owner_id]
            )
            owner_id_db, owner_wallet, owner_agreement = res.fetchone()
            
            # Save file
            filename = basename(file.filename)
            ext = filename.split(".")[-1]
            new_file_name = uuid4().hex + "." + ext
            new_file_location = join(settings.IMAGES_DIR, new_file_name)
            
            with open(new_file_location, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # Create AssetAgreement if not exists
            if owner_agreement is None:
                factory = AssetFactory(
                    LOCAL_ENDPOINT,
                    settings.FACTORY_CONTRACT_ADDRESS,
                    owner_wallet
                )
                owner_agreement, _ = factory.deploy_asset_agreement(
                    "ASSET", "ASSET", settings.MARKET_CONTRACT_ADDRESS
                )
                agreement = AssetAgreement(
                    LOCAL_ENDPOINT, owner_agreement, owner_wallet
                )
                agreement.set_approval_for_all(settings.MARKET_CONTRACT_ADDRESS, True)
                
                con.execute(
                    "UPDATE users SET agreement = ? WHERE id = ?",
                    [owner_agreement, owner_id_db]
                )
                con.commit()
            
            # Mint NFT
            agreement = AssetAgreement(
                LOCAL_ENDPOINT, owner_agreement, owner_wallet
            )
            token_id = agreement.get_next_token_id()
            agreement.mint([price], [resale_allowed])
            
            # Insert to database
            con.execute(
                "INSERT INTO assets (owner_id, filepath, token_id) VALUES (?, ?, ?)",
                [owner_id_db, new_file_location, token_id]
            )
            con.commit()
            
            return AssetResponse(
                id=con.lastrowid,
                owner_id=owner_id_db,
                filepath=new_file_location,
                token_id=token_id,
                price=price,
                for_sale=True,
                resale_allowed=resale_allowed,
                owner_name="",  # Can be fetched separately
                agreement_address=owner_agreement
            )
        finally:
            con.close()
    
    def get_all_assets(self) -> List[AssetResponse]:
        """Get all assets"""
        con = get_demo_db()
        try:
            res = con.execute(
                """SELECT assets.id, assets.owner_id, assets.filepath, 
                   assets.token_id, users.uname, users.agreement
                   FROM assets 
                   LEFT JOIN users ON assets.owner_id = users.id"""
            )
            assets = []
            for row in res.fetchall():
                assets.append(AssetResponse(
                    id=row[0],
                    owner_id=row[1],
                    filepath=row[2],
                    token_id=row[3],
                    owner_name=row[4],
                    agreement_address=row[5],
                    price=0.0,  # Fetch from blockchain
                    for_sale=False,
                    resale_allowed=False
                ))
            return assets
        finally:
            con.close()
    
    def get_asset_metadata(
        self,
        agreement_address: str,
        token_id: int
    ) -> AssetMetadata:
        """Get asset metadata from blockchain"""
        agreement = AssetAgreement(LOCAL_ENDPOINT, agreement_address)
        price, asset_hash, for_sale, resale_allowed = agreement.fetch_asset_metadata(token_id)
        
        return AssetMetadata(
            price=price,
            asset_hash=asset_hash.hex() if asset_hash else None,
            for_sale=for_sale,
            resale_allowed=resale_allowed
        )
```

### `backend/app/services/market_service.py`

```python
from app.db import get_demo_db
from app.contract import AssetAgreement, AssetMarket
from app.constants import LOCAL_ENDPOINT
from app.config import settings
from app.models.transaction import PurchaseResponse
from tempfile import NamedTemporaryFile
from Crypto.Hash import SHA256
from lsb_watermarking.main_multibit import Watermark
import os

class MarketService:
    def purchase_asset(
        self,
        agreement_address: str,
        token_id: int,
        buyer_id: int
    ) -> PurchaseResponse:
        """Purchase asset - migrated from Market.on_image_buy()"""
        con = get_demo_db()
        try:
            # Get asset info
            agreement = AssetAgreement(LOCAL_ENDPOINT, agreement_address)
            asset_price = agreement.price_of(token_id)
            seller_address = agreement.owner_of(token_id)
            
            # Get seller_id
            res = con.execute(
                "SELECT id FROM users WHERE wallet = ?",
                [seller_address]
            )
            seller_id, = res.fetchone()
            
            # Get image location
            res = con.execute(
                """SELECT assets.filepath FROM users 
                   LEFT JOIN assets ON users.id = assets.owner_id 
                   WHERE users.agreement = ? AND assets.token_id = ?""",
                [agreement_address, token_id]
            )
            img_location, = res.fetchone()
            
            # Create watermark
            wm_image = NamedTemporaryFile("wb", suffix=".png", delete=False)
            with open(img_location, "rb") as f:
                data = f.read()
                wm_image.write(data)
                cipher = SHA256.new(data)
                cipher.update(bytes([seller_id, buyer_id]))
                img_hash = cipher.digest()
                img_hash_hex = cipher.hexdigest()
            
            wm_file_name = wm_image.name
            wm_image.close()
            
            # Watermark image
            wm = Watermark()
            wm.set_watermark(seller_id, buyer_id)
            wm.watermark_image(wm_file_name)
            
            # Update hash on blockchain
            market_manager = AssetMarket(
                LOCAL_ENDPOINT,
                settings.MARKET_CONTRACT_ADDRESS,
                settings.MANAGER_ADDRESS
            )
            market_manager.update_hash(agreement_address, token_id, img_hash)
            
            # Execute purchase
            res = con.execute("SELECT wallet FROM users WHERE id = ?", [buyer_id])
            buyer_wallet_address, = res.fetchone()
            
            asset_market = AssetMarket(
                LOCAL_ENDPOINT,
                settings.MARKET_CONTRACT_ADDRESS,
                buyer_wallet_address
            )
            tx_receipt = asset_market.purchase(
                agreement_address, token_id, asset_price
            )
            
            # Save watermarked file
            watermarked_filename = f"watermarked_{token_id}_{buyer_id}.png"
            watermarked_path = os.path.join(settings.IMAGES_DIR, watermarked_filename)
            os.rename(wm_file_name, watermarked_path)
            
            return PurchaseResponse(
                transaction_hash=tx_receipt.transactionHash.hex(),
                watermarked_file_url=f"/static/{watermarked_filename}",
                asset_hash=img_hash_hex,
                message="Purchase successful"
            )
        finally:
            con.close()
    
    def get_marketplace_assets(self):
        """Get all assets available for sale"""
        # Implementation similar to Market.render()
        # Return list of assets with metadata
        pass
```

## Bước 7: Migration Utilities

### `backend/app/utils/web3_utils.py`

```python
from web3 import Web3
from app.config import settings

_web3_provider = None

def get_web3_provider():
    """Get Web3 provider singleton"""
    global _web3_provider
    if _web3_provider is None or not _web3_provider.isConnected():
        _web3_provider = Web3(Web3.HTTPProvider(
            settings.ETH_ENDPOINT,
            request_kwargs={'verify': False}
        ))
    return _web3_provider
```

## Bước 8: Chạy FastAPI Server

### Development

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Bước 9: Frontend Integration

### Example: React Frontend

#### `frontend/src/services/api.js`

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  // Users
  registerUser: async (name, wallet) => {
    const response = await fetch(`${API_BASE_URL}/users/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uname: name, wallet })
    });
    return response.json();
  },

  getUsers: async () => {
    const response = await fetch(`${API_BASE_URL}/users/`);
    return response.json();
  },

  // Assets
  publishAsset: async (ownerId, price, resaleAllowed, file) => {
    const formData = new FormData();
    formData.append('owner_id', ownerId);
    formData.append('price', price);
    formData.append('resale_allowed', resaleAllowed);
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/assets/publish`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  },

  getAssetsForSale: async () => {
    const response = await fetch(`${API_BASE_URL}/assets/for-sale`);
    return response.json();
  },

  // Market
  purchaseAsset: async (agreementAddress, tokenId, buyerId) => {
    const response = await fetch(`${API_BASE_URL}/market/purchase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agreement_address: agreementAddress,
        token_id: tokenId,
        buyer_id: buyerId
      })
    });
    return response.json();
  },

  // Watermark
  extractWatermark: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/watermark/extract`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
};
```

#### `frontend/src/components/UserRegistration.jsx`

```jsx
import { useState } from 'react';
import { api } from '../services/api';

function UserRegistration() {
  const [name, setName] = useState('');
  const [wallet, setWallet] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await api.registerUser(name, wallet);
      setMessage(`${result.uname} has been registered!`);
      setName('');
      setWallet('');
    } catch (error) {
      setMessage('Registration failed: ' + error.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>User Registration</h2>
      <input
        type="text"
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <input
        type="text"
        placeholder="Wallet Address"
        value={wallet}
        onChange={(e) => setWallet(e.target.value)}
      />
      <button type="submit">Register</button>
      {message && <p>{message}</p>}
    </form>
  );
}

export default UserRegistration;
```

## Bước 10: Testing

### Unit Tests Example

```python
# backend/tests/test_user_service.py
import pytest
from app.services.user_service import UserService

def test_register_user():
    service = UserService()
    result = service.register_user("test_user", "0x123...")
    assert result == True

def test_register_duplicate_user():
    service = UserService()
    service.register_user("test_user", "0x123...")
    result = service.register_user("test_user", "0x456...")
    assert result == False
```

### API Tests Example

```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/api/users/register",
        json={"uname": "test", "wallet": "0x123..."}
    )
    assert response.status_code == 200
    assert response.json()["uname"] == "test"
```

## Bước 11: Environment Configuration

### `backend/.env`

```env
ETH_ENDPOINT=http://127.0.0.1:8545/
MARKET_CONTRACT_ADDRESS=0x...
FACTORY_CONTRACT_ADDRESS=0x...
DATABASE_PATH=src/db/demo.db
IMAGES_DIR=images
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Bước 12: Migration Checklist

- [ ] Cài đặt FastAPI và dependencies
- [ ] Tạo cấu trúc thư mục backend
- [ ] Tạo FastAPI app và config
- [ ] Tạo Pydantic models
- [ ] Tạo API routes cho tất cả endpoints
- [ ] Migrate business logic từ Streamlit modules sang services
- [ ] Test tất cả API endpoints
- [ ] Setup CORS cho frontend
- [ ] Tạo frontend application
- [ ] Integrate frontend với API
- [ ] Test end-to-end
- [ ] Update documentation
- [ ] Deploy backend và frontend

## Lưu Ý Quan Trọng

1. **File Uploads**: Sử dụng `UploadFile` từ FastAPI, không dùng Streamlit's `st.file_uploader`
2. **Session State**: Streamlit's `st.session_state` không có trong FastAPI, cần dùng JWT tokens hoặc session cookies
3. **Real-time Updates**: Streamlit tự động refresh, frontend cần polling hoặc WebSocket
4. **Error Handling**: FastAPI trả về HTTP status codes, frontend cần handle errors
5. **Authentication**: Thêm JWT authentication nếu cần
6. **File Storage**: Cân nhắc dùng cloud storage (S3, IPFS) thay vì local files

## Tài Liệu Tham Khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [CORS in FastAPI](https://fastapi.tiangolo.com/tutorial/cors/)
- [File Uploads in FastAPI](https://fastapi.tiangolo.com/tutorial/request-files/)

## Hỗ Trợ

Nếu gặp vấn đề trong quá trình migration, kiểm tra:
1. CORS configuration
2. File paths và permissions
3. Database connections
4. Web3 provider connections
5. Contract addresses

