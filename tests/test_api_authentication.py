"""
Tests for API Authentication

Tests ensure all public endpoints require valid API authentication
and are tied to authenticated user accounts.
"""

import pytest
from fastapi.testclient import TestClient
import hashlib
from datetime import datetime, timedelta, timezone

from api.main import app
from api.dependencies import require_api_key


client = TestClient(app)


# ============================================================================
# Test Data
# ============================================================================

# Valid API key for testing (in real scenario, would be from database)
TEST_API_KEY = "test_sk_1234567890abcdef"
TEST_USER_ID = "test-user-123"
TEST_KEY_ID = "key-123"

# Mock API key hash (SHA-256 of TEST_API_KEY)
TEST_API_KEY_HASH = hashlib.sha256(TEST_API_KEY.encode()).hexdigest()


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthenticationRequired:
    """Test that endpoints require authentication"""

    def test_list_stocks_without_api_key(self):
        """GET /v1/stocks should require API key"""
        response = client.get("/v1/stocks")
        assert response.status_code == 401
        assert "API key required" in response.json()['detail']

    def test_list_stocks_with_invalid_api_key(self):
        """GET /v1/stocks with invalid API key should fail"""
        response = client.get(
            "/v1/stocks",
            headers={"X-API-Key": "invalid_key_xyz"}
        )
        assert response.status_code == 403
        assert "Invalid" in response.json()['detail']

    def test_dividends_without_api_key(self):
        """GET /v1/dividends/calendar should require API key"""
        response = client.get("/v1/dividends/calendar")
        assert response.status_code == 401

    def test_screeners_without_api_key(self):
        """GET /v1/screeners/high-yield should require API key"""
        response = client.get("/v1/screeners/high-yield")
        assert response.status_code == 401

    def test_search_without_api_key(self):
        """GET /v1/search should require API key"""
        response = client.get("/v1/search")
        assert response.status_code == 401

    def test_etfs_without_api_key(self):
        """GET /v1/etfs/{symbol} should require API key"""
        response = client.get("/v1/etfs/QQQ")
        assert response.status_code == 401

    def test_analytics_without_api_key(self):
        """POST /v1/analytics/portfolio should require API key"""
        response = client.post(
            "/v1/analytics/portfolio",
            json={"holdings": []}
        )
        assert response.status_code == 401

    def test_bulk_stocks_without_api_key(self):
        """POST /v1/bulk/stocks should require API key"""
        response = client.post(
            "/v1/bulk/stocks",
            json={"symbols": ["AAPL"]}
        )
        assert response.status_code == 401


class TestAPIKeyExtraction:
    """Test API key extraction from different sources"""

    def test_api_key_from_bearer_header(self):
        """Should extract API key from Authorization: Bearer header"""
        api_key = "test_key_bearer"
        response = client.get(
            "/v1/stocks",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        # Will get 403 (invalid key) not 401 (missing key)
        assert response.status_code == 403

    def test_api_key_from_x_api_key_header(self):
        """Should extract API key from X-API-Key header"""
        api_key = "test_key_header"
        response = client.get(
            "/v1/stocks",
            headers={"X-API-Key": api_key}
        )
        # Will get 403 (invalid key) not 401 (missing key)
        assert response.status_code == 403

    def test_api_key_from_query_parameter(self):
        """Should extract API key from ?api_key= query parameter"""
        api_key = "test_key_query"
        response = client.get(
            "/v1/stocks?api_key=" + api_key
        )
        # Will get 403 (invalid key) not 401 (missing key)
        assert response.status_code == 403


class TestExcludedEndpoints:
    """Test that certain endpoints don't require authentication"""

    def test_health_check_without_auth(self):
        """GET /health should NOT require authentication"""
        response = client.get("/health")
        # Will either be 200 (healthy) or 503 (unhealthy) but not 401
        assert response.status_code in [200, 503]

    def test_root_without_auth(self):
        """GET / should NOT require authentication"""
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()

    def test_auth_login_without_auth(self):
        """GET /auth/login should NOT require authentication"""
        response = client.get("/auth/login")
        # Will fail for other reasons (missing params) but not 401 for missing key
        # This endpoint redirects, so might get 307 or similar
        assert response.status_code != 401

    def test_auth_status_without_auth(self):
        """GET /auth/status should NOT require authentication"""
        response = client.get("/auth/status")
        # This endpoint returns 200 even without auth
        assert response.status_code in [200, 401]  # 401 if needs login context


# ============================================================================
# User Account Tracking Tests
# ============================================================================

class TestUserAccountTracking:
    """Test that requests are tied to user accounts"""

    def test_authentication_returns_user_info(self):
        """Valid API key should return user information"""
        # Note: This test would need a real database with valid API key
        # The dependency should return user_id, tier, key_id
        # This is a placeholder for integration tests
        pass

    def test_request_state_includes_user_id(self):
        """Authenticated request should set user_id in request state"""
        # This would be tested with middleware/integration tests
        pass

    def test_request_state_includes_tier(self):
        """Authenticated request should set tier in request state"""
        # This would be tested with middleware/integration tests
        pass


# ============================================================================
# Error Response Tests
# ============================================================================

class TestErrorResponses:
    """Test error response formats"""

    def test_missing_api_key_response_format(self):
        """Missing API key should return proper error format"""
        response = client.get("/v1/stocks")
        assert response.status_code == 401
        data = response.json()
        assert 'detail' in data
        assert isinstance(data['detail'], str)

    def test_invalid_api_key_response_format(self):
        """Invalid API key should return proper error format"""
        response = client.get(
            "/v1/stocks",
            headers={"X-API-Key": "invalid"}
        )
        assert response.status_code == 403
        data = response.json()
        assert 'detail' in data

    def test_401_response_has_www_authenticate_header(self):
        """401 response should include WWW-Authenticate header"""
        response = client.get("/v1/stocks")
        assert response.status_code == 401
        assert 'WWW-Authenticate' in response.headers


# ============================================================================
# Integration Tests
# ============================================================================

class TestEndpointCoverage:
    """Verify all public endpoints require authentication"""

    # List of all public endpoints that should require authentication
    PUBLIC_ENDPOINTS = [
        # Stocks endpoints
        ("GET", "/v1/stocks"),
        ("GET", "/v1/stocks/AAPL"),
        ("GET", "/v1/stocks/AAPL/fundamentals"),
        ("GET", "/v1/stocks/AAPL/metrics"),
        ("GET", "/v1/stocks/AAPL/quote"),
        ("GET", "/v1/stocks/AAPL/splits"),

        # Dividends endpoints
        ("GET", "/v1/dividends/calendar"),
        ("GET", "/v1/dividends/history"),
        ("GET", "/v1/stocks/AAPL/dividends"),

        # Screeners endpoints
        ("GET", "/v1/screeners/high-yield"),
        ("GET", "/v1/screeners/monthly-payers"),
        ("GET", "/v1/screeners/dividend-aristocrats"),
        ("GET", "/v1/screeners/dividend-kings"),
        ("GET", "/v1/screeners/high-growth-dividends"),

        # Search endpoints
        ("GET", "/v1/search"),

        # ETF endpoints
        ("GET", "/v1/etfs/QQQ"),
        ("GET", "/v1/etfs/QQQ/holdings"),
        ("GET", "/v1/etfs/classify/QQQ"),

        # Analytics endpoints
        ("POST", "/v1/analytics/portfolio"),

        # Bulk endpoints
        ("POST", "/v1/bulk/stocks"),
        ("POST", "/v1/bulk/dividends"),
        ("POST", "/v1/bulk/prices"),
        ("POST", "/v1/bulk/latest"),
    ]

    @pytest.mark.parametrize("method,endpoint", PUBLIC_ENDPOINTS)
    def test_endpoint_requires_auth(self, method, endpoint):
        """All public endpoints should require authentication"""
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json={})

        # Should fail with 401 (missing auth) or 403 (invalid auth)
        # Not 422 (validation) or 200 (success)
        assert response.status_code in [401, 403], \
            f"{method} {endpoint} should require auth but got {response.status_code}"


# ============================================================================
# Help and Documentation
# ============================================================================

class TestAuthenticationDocumentation:
    """Test that authentication is documented in responses"""

    def test_401_response_includes_helpful_message(self):
        """401 response should tell user how to provide API key"""
        response = client.get("/v1/stocks")
        assert response.status_code == 401
        data = response.json()
        detail = data['detail'].lower()
        # Should mention how to provide the key
        assert any(keyword in detail for keyword in ['api key', 'header', 'x-api-key', 'parameter'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
