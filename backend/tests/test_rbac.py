"""
Role-Based Access Control (RBAC) tests for FleetWise application.

Tests authorization decorators and role-based permissions
as specified in Phase 5 security requirements.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.permissions import require_role, require_any_role
from app.core.security import create_access_token
from app.core.dependencies import get_current_user


client = TestClient(app)


class TestRoleBasedAccess:
    """Test role-based access control decorators"""
    
    def create_test_token(self, user_data):
        """Helper method to create test JWT tokens"""
        return create_access_token(data=user_data)
    
    def get_auth_headers(self, token):
        """Helper method to create authorization headers"""
        return {"Authorization": f"Bearer {token}"}


class TestFleetManagerAccess:
    """Test Fleet Manager role permissions"""
    
    def test_manager_can_create_vehicle(self):
        """Test that Fleet Manager can create vehicles"""
        # Create Fleet Manager token
        manager_token = create_access_token(data={
            "user_id": 1,
            "email": "manager@fleet.com", 
            "role": "FLEET_MANAGER"
        })
        
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Test POST /vehicles endpoint
        vehicle_data = {
            "manufacturer": "Toyota",
            "model": "Camry",
            "license_plate": "TEST-001"
        }
        
        response = client.post("/vehicles", json=vehicle_data, headers=headers)
        
        # Should succeed (status 200/201) or fail for business reasons, not authorization
        assert response.status_code != 403  # Not forbidden
        assert response.status_code != 401  # Not unauthorized
    
    def test_manager_can_delete_vehicle(self):
        """Test that Fleet Manager can delete vehicles"""
        manager_token = create_access_token(data={
            "user_id": 1,
            "email": "manager@fleet.com",
            "role": "FLEET_MANAGER"
        })
        
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Test DELETE /vehicles/{id} endpoint
        response = client.delete("/vehicles/1", headers=headers)
        
        # Should not be forbidden due to role
        assert response.status_code != 403
        assert response.status_code != 401
    
    def test_manager_can_create_reservation(self):
        """Test that Fleet Manager can create reservations"""
        manager_token = create_access_token(data={
            "user_id": 1,
            "email": "manager@fleet.com",
            "role": "FLEET_MANAGER"
        })
        
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        reservation_data = {
            "user_id": 2,
            "vehicle_id": 1
        }
        
        response = client.post("/reservations", json=reservation_data, headers=headers)
        
        # Should not be forbidden due to role
        assert response.status_code != 403
        assert response.status_code != 401
    
    def test_manager_can_process_return(self):
        """Test that Fleet Manager can process vehicle returns"""
        manager_token = create_access_token(data={
            "user_id": 1,
            "email": "manager@fleet.com",
            "role": "FLEET_MANAGER"
        })
        
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        response = client.put("/reservations/1/return", headers=headers)
        
        # Should not be forbidden due to role
        assert response.status_code != 403
        assert response.status_code != 401


class TestFleetUserRestrictions:
    """Test Fleet User role restrictions"""
    
    def test_user_cannot_create_vehicle(self):
        """Test that Fleet User cannot create vehicles"""
        user_token = create_access_token(data={
            "user_id": 2,
            "email": "user@fleet.com",
            "role": "FLEET_USER"
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        vehicle_data = {
            "manufacturer": "Honda",
            "model": "Accord",
            "license_plate": "USER-001"
        }
        
        response = client.post("/vehicles", json=vehicle_data, headers=headers)
        
        # Should be forbidden
        assert response.status_code == 403
        assert "permission" in response.json().get("detail", "").lower()
    
    def test_user_cannot_delete_vehicle(self):
        """Test that Fleet User cannot delete vehicles"""
        user_token = create_access_token(data={
            "user_id": 2,
            "email": "user@fleet.com",
            "role": "FLEET_USER"
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = client.delete("/vehicles/1", headers=headers)
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_user_cannot_create_reservation(self):
        """Test that Fleet User cannot directly create reservations"""
        user_token = create_access_token(data={
            "user_id": 2,
            "email": "user@fleet.com",
            "role": "FLEET_USER"
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        reservation_data = {
            "user_id": 2,
            "vehicle_id": 1
        }
        
        response = client.post("/reservations", json=reservation_data, headers=headers)
        
        # Should be forbidden - only managers can create reservations
        assert response.status_code == 403
    
    def test_user_can_view_own_reservations(self):
        """Test that Fleet User can view their own reservations"""
        user_token = create_access_token(data={
            "user_id": 2,
            "email": "user@fleet.com",
            "role": "FLEET_USER"
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = client.get("/reservations", headers=headers)
        
        # Should be allowed to view own reservations
        assert response.status_code != 403
        assert response.status_code != 401


class TestUnauthorizedAccess:
    """Test unauthorized access scenarios"""
    
    def test_no_token_gets_401(self):
        """Test that requests without token get 401 Unauthorized"""
        # Try to access protected endpoint without token
        response = client.get("/vehicles")
        
        assert response.status_code == 401
    
    def test_invalid_token_gets_401(self):
        """Test that requests with invalid token get 401 Unauthorized"""
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        
        response = client.get("/vehicles", headers=invalid_headers)
        
        assert response.status_code == 401
    
    def test_expired_token_gets_401(self):
        """Test that expired tokens are rejected"""
        # Create token with past expiration
        from datetime import datetime, timedelta
        import jwt
        from app.core.config import settings
        
        expired_payload = {
            "user_id": 1,
            "email": "test@fleet.com",
            "role": "FLEET_USER",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/vehicles", headers=headers)
        
        assert response.status_code == 401
    
    def test_wrong_role_gets_403(self):
        """Test that insufficient permissions return 403 Forbidden"""
        # Fleet User trying to access manager-only endpoint
        user_token = create_access_token(data={
            "user_id": 2,
            "email": "user@fleet.com",
            "role": "FLEET_USER"
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Try to create vehicle (manager-only operation)
        vehicle_data = {
            "manufacturer": "Toyota",
            "model": "Camry", 
            "license_plate": "FORBIDDEN"
        }
        
        response = client.post("/vehicles", json=vehicle_data, headers=headers)
        
        assert response.status_code == 403


class TestRoleDecorators:
    """Test the role decorator functions directly"""
    
    @pytest.fixture
    def mock_current_user_fleet_manager(self):
        """Mock current user as Fleet Manager"""
        return {
            "user_id": 1,
            "email": "manager@fleet.com",
            "role": "FLEET_MANAGER"
        }
    
    @pytest.fixture
    def mock_current_user_fleet_user(self):
        """Mock current user as Fleet User"""
        return {
            "user_id": 2,
            "email": "user@fleet.com", 
            "role": "FLEET_USER"
        }
    
    def test_require_role_decorator_allows_correct_role(self, mock_current_user_fleet_manager):
        """Test that require_role decorator allows correct role"""
        
        @require_role("FLEET_MANAGER")
        async def test_endpoint(current_user):
            return {"message": "success"}
        
        # Should not raise exception for correct role
        result = test_endpoint(mock_current_user_fleet_manager)
        assert result["message"] == "success"
    
    def test_require_role_decorator_blocks_incorrect_role(self, mock_current_user_fleet_user):
        """Test that require_role decorator blocks incorrect role"""
        
        @require_role("FLEET_MANAGER")
        async def test_endpoint(current_user):
            return {"message": "success"}
        
        # Should raise HTTPException for incorrect role
        with pytest.raises(HTTPException) as exc_info:
            test_endpoint(mock_current_user_fleet_user)
        
        assert exc_info.value.status_code == 403
        assert "permission" in exc_info.value.detail.lower()
    
    def test_require_any_role_decorator(self, mock_current_user_fleet_user, mock_current_user_fleet_manager):
        """Test that require_any_role decorator works with multiple allowed roles"""
        
        @require_any_role(["FLEET_MANAGER", "FLEET_USER"])
        async def test_endpoint(current_user):
            return {"message": "success"}
        
        # Should allow both Fleet Manager and Fleet User
        result1 = test_endpoint(mock_current_user_fleet_manager)
        assert result1["message"] == "success"
        
        result2 = test_endpoint(mock_current_user_fleet_user)
        assert result2["message"] == "success"
    
    def test_require_any_role_blocks_unknown_role(self):
        """Test that require_any_role blocks unknown roles"""
        
        @require_any_role(["FLEET_MANAGER", "FLEET_USER"])
        async def test_endpoint(current_user):
            return {"message": "success"}
        
        unknown_role_user = {
            "user_id": 99,
            "email": "admin@fleet.com",
            "role": "UNKNOWN_ROLE"
        }
        
        # Should raise HTTPException for unknown role
        with pytest.raises(HTTPException) as exc_info:
            test_endpoint(unknown_role_user)
        
        assert exc_info.value.status_code == 403


class TestChatbotAccess:
    """Test chatbot endpoint access control"""
    
    def test_fleet_user_can_use_chatbot(self):
        """Test that Fleet Users can access chatbot"""
        user_token = create_access_token(data={
            "user_id": 2,
            "email": "user@fleet.com",
            "role": "FLEET_USER"
        })
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test chatbot endpoints
        response = client.get("/chatbot/manufacturers", headers=headers)
        assert response.status_code != 403
        assert response.status_code != 401
        
        response = client.get("/chatbot/models?manufacturer=Toyota", headers=headers)
        assert response.status_code != 403
        assert response.status_code != 401
    
    def test_fleet_manager_can_use_chatbot(self):
        """Test that Fleet Managers can also access chatbot"""
        manager_token = create_access_token(data={
            "user_id": 1,
            "email": "manager@fleet.com",
            "role": "FLEET_MANAGER"
        })
        
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        response = client.get("/chatbot/manufacturers", headers=headers)
        assert response.status_code != 403
        assert response.status_code != 401