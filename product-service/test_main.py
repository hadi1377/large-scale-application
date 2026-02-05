import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from datetime import datetime

from main import app, product_to_dict
from database import get_database


@pytest.fixture
def mock_database():
    """Mock MongoDB database"""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.products = mock_collection
    return mock_db, mock_collection


@pytest.fixture
def client(mock_database):
    mock_db, mock_collection = mock_database
    with patch('main.get_database', return_value=mock_db):
        yield TestClient(app)


@pytest.fixture
def sample_product():
    """Sample product data"""
    return {
        "_id": ObjectId(),
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 50,
        "category": "Electronics",
        "properties": {"color": "red", "size": "large"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.mark.asyncio
class TestCreateProduct:
    """Test product creation"""
    
    async def test_create_product_success(self, client, mock_database, sample_product):
        """Test successful product creation"""
        mock_db, mock_collection = mock_database
        
        # Mock insert_one
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=sample_product["_id"]))
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        
        response = client.post(
            "/products",
            json={
                "name": "Test Product",
                "description": "Test Description",
                "price": 99.99,
                "stock": 50,
                "category": "Electronics",
                "properties": {"color": "red", "size": "large"}
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["price"] == 99.99
        assert data["stock"] == 50
        assert "id" in data
    
    async def test_create_product_minimal(self, client, mock_database, sample_product):
        """Test product creation with minimal fields"""
        mock_db, mock_collection = mock_database
        sample_product["description"] = None
        sample_product["category"] = None
        sample_product["properties"] = None
        
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=sample_product["_id"]))
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        
        response = client.post(
            "/products",
            json={
                "name": "Test Product",
                "price": 99.99,
                "stock": 50
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
    
    async def test_create_product_invalid_price(self, client):
        """Test product creation with invalid price"""
        response = client.post(
            "/products",
            json={
                "name": "Test Product",
                "price": -10,
                "stock": 50
            }
        )
        assert response.status_code == 422
    
    async def test_create_product_invalid_stock(self, client):
        """Test product creation with invalid stock"""
        response = client.post(
            "/products",
            json={
                "name": "Test Product",
                "price": 99.99,
                "stock": -5
            }
        )
        assert response.status_code == 422
    
    async def test_create_product_missing_fields(self, client):
        """Test product creation with missing required fields"""
        response = client.post(
            "/products",
            json={
                "name": "Test Product"
            }
        )
        assert response.status_code == 422
    
    async def test_create_product_empty_name(self, client):
        """Test product creation with empty name"""
        response = client.post(
            "/products",
            json={
                "name": "",
                "price": 99.99,
                "stock": 50
            }
        )
        assert response.status_code == 422
    
    async def test_create_product_no_database(self, client):
        """Test product creation when database is unavailable"""
        with patch('main.get_database', return_value=None):
            response = client.post(
                "/products",
                json={
                    "name": "Test Product",
                    "price": 99.99,
                    "stock": 50
                }
            )
            assert response.status_code == 500


@pytest.mark.asyncio
class TestGetProducts:
    """Test getting products list"""
    
    async def test_get_products_success(self, client, mock_database, sample_product):
        """Test successful product list retrieval"""
        mock_db, mock_collection = mock_database
        products = [sample_product]
        
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=products)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        response = client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Test Product"
    
    async def test_get_products_with_pagination(self, client, mock_database, sample_product):
        """Test product list with pagination"""
        mock_db, mock_collection = mock_database
        products = [sample_product]
        
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=products)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        response = client.get("/products?skip=10&limit=5")
        assert response.status_code == 200
    
    async def test_get_products_with_category_filter(self, client, mock_database, sample_product):
        """Test product list with category filter"""
        mock_db, mock_collection = mock_database
        products = [sample_product]
        
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=products)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        response = client.get("/products?category=Electronics")
        assert response.status_code == 200
    
    async def test_get_products_with_price_filter(self, client, mock_database, sample_product):
        """Test product list with price filter"""
        mock_db, mock_collection = mock_database
        products = [sample_product]
        
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=products)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        response = client.get("/products?min_price=50&max_price=100")
        assert response.status_code == 200
    
    async def test_get_products_invalid_limit(self, client):
        """Test product list with invalid limit"""
        response = client.get("/products?limit=0")
        assert response.status_code == 422
    
    async def test_get_products_no_database(self, client):
        """Test product list when database is unavailable"""
        with patch('main.get_database', return_value=None):
            response = client.get("/products")
            assert response.status_code == 500


@pytest.mark.asyncio
class TestGetProduct:
    """Test getting single product"""
    
    async def test_get_product_success(self, client, mock_database, sample_product):
        """Test successful product retrieval"""
        mock_db, mock_collection = mock_database
        product_id = str(sample_product["_id"])
        
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Test Product"
    
    async def test_get_product_not_found(self, client, mock_database):
        """Test getting non-existent product"""
        mock_db, mock_collection = mock_database
        product_id = str(ObjectId())
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 404
    
    async def test_get_product_invalid_id(self, client):
        """Test getting product with invalid ID format"""
        response = client.get("/products/invalid-id")
        assert response.status_code == 400
    
    async def test_get_product_no_database(self, client):
        """Test getting product when database is unavailable"""
        with patch('main.get_database', return_value=None):
            response = client.get(f"/products/{str(ObjectId())}")
            assert response.status_code == 500


@pytest.mark.asyncio
class TestUpdateProduct:
    """Test product update"""
    
    async def test_update_product_success(self, client, mock_database, sample_product):
        """Test successful product update"""
        mock_db, mock_collection = mock_database
        product_id = str(sample_product["_id"])
        updated_product = {**sample_product, "name": "Updated Product", "price": 149.99}
        
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        mock_collection.update_one = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=updated_product)
        
        response = client.put(
            f"/products/{product_id}",
            json={
                "name": "Updated Product",
                "price": 149.99
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert data["price"] == 149.99
    
    async def test_update_product_partial(self, client, mock_database, sample_product):
        """Test partial product update"""
        mock_db, mock_collection = mock_database
        product_id = str(sample_product["_id"])
        updated_product = {**sample_product, "stock": 100}
        
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        mock_collection.update_one = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=updated_product)
        
        response = client.put(
            f"/products/{product_id}",
            json={
                "stock": 100
            }
        )
        assert response.status_code == 200
    
    async def test_update_product_not_found(self, client, mock_database):
        """Test updating non-existent product"""
        mock_db, mock_collection = mock_database
        product_id = str(ObjectId())
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        response = client.put(
            f"/products/{product_id}",
            json={
                "name": "Updated Product"
            }
        )
        assert response.status_code == 404
    
    async def test_update_product_invalid_id(self, client):
        """Test updating product with invalid ID"""
        response = client.put(
            "/products/invalid-id",
            json={
                "name": "Updated Product"
            }
        )
        assert response.status_code == 400
    
    async def test_update_product_no_fields(self, client, mock_database, sample_product):
        """Test update with no fields provided"""
        mock_db, mock_collection = mock_database
        product_id = str(sample_product["_id"])
        
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        
        response = client.put(
            f"/products/{product_id}",
            json={}
        )
        assert response.status_code == 400
    
    async def test_update_product_invalid_price(self, client, mock_database, sample_product):
        """Test update with invalid price"""
        mock_db, mock_collection = mock_database
        product_id = str(sample_product["_id"])
        
        mock_collection.find_one = AsyncMock(return_value=sample_product)
        
        response = client.put(
            f"/products/{product_id}",
            json={
                "price": -10
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestDeleteProduct:
    """Test product deletion"""
    
    async def test_delete_product_success(self, client, mock_database, sample_product):
        """Test successful product deletion"""
        mock_db, mock_collection = mock_database
        product_id = str(sample_product["_id"])
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 204
    
    async def test_delete_product_not_found(self, client, mock_database):
        """Test deleting non-existent product"""
        mock_db, mock_collection = mock_database
        product_id = str(ObjectId())
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 404
    
    async def test_delete_product_invalid_id(self, client):
        """Test deleting product with invalid ID"""
        response = client.delete("/products/invalid-id")
        assert response.status_code == 400
    
    async def test_delete_product_no_database(self, client):
        """Test deleting product when database is unavailable"""
        with patch('main.get_database', return_value=None):
            response = client.delete(f"/products/{str(ObjectId())}")
            assert response.status_code == 500


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test root endpoint"""
    
    async def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"service": "product-service"}


@pytest.mark.asyncio
class TestProductToDict:
    """Test product_to_dict helper function"""
    
    async def test_product_to_dict(self, sample_product):
        """Test product dictionary conversion"""
        # Make a copy since product_to_dict modifies the dict in place
        product_copy = sample_product.copy()
        product_id = str(product_copy["_id"])
        
        result = product_to_dict(product_copy)
        assert "id" in result
        assert result["id"] == product_id
        assert "_id" not in result

