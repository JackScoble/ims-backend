"""
Authentication and Security tests for the Inventory Management System API.
Validates that endpoints are properly secured, tokens are required, and 
user credential management workflows operate safely.
"""

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class AuthenticationTests(APITestCase):
    """
    Test suite validating endpoint security and password management logic.
    """
    
    def setUp(self):
        """
        Initializes the test environment with a standard user account and 
        defines the protected API endpoints to be tested.
        """
        self.user = User.objects.create_user(username='testuser', password='oldpassword123')
        self.items_url = '/api/items/'
        self.change_pwd_url = '/api/password_change/'

    def test_unauthenticated_user_cannot_access_items(self):
        """
        Validates global API security.
        Ensures that requests lacking a valid authentication token are immediately
        blocked and return a 401 Unauthorized status.
        """
        response = self.client.get(self.items_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_access_items(self):
        """
        Validates token authorization mapping.
        Ensures that requests containing a valid authentication token are successfully
        routed and return a 200 OK status.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.items_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_change_fails_with_wrong_old_password(self):
        """
        Validates the credential update workflow.
        Ensures that a user cannot update their password unless they accurately
        provide their current existing password, returning a 400 Bad Request on failure.
        """
        self.client.force_authenticate(user=self.user)
        payload = {
            "old_password": "wrongpassword",
            "new_password": "NewStrongPassword123!"
        }
        response = self.client.put(self.change_pwd_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)