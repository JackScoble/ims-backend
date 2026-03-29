from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='oldpassword123')
        self.items_url = '/api/items/'
        self.change_pwd_url = '/api/password_change/'

    def test_unauthenticated_user_cannot_access_items(self):
        """Security: Ensure unauthenticated requests are blocked with 401 Unauthorized."""
        response = self.client.get(self.items_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_access_items(self):
        """Security: Ensure valid tokens grant access."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.items_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_change_fails_with_wrong_old_password(self):
        """Auth Workflow: Ensure password change rejects invalid current passwords."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "old_password": "wrongpassword",
            "new_password": "NewStrongPassword123!"
        }
        response = self.client.put(self.change_pwd_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)