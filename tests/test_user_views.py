from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.users.models import UserModel

class UserAPITest(APITestCase):

    def setUp(self):
        self.user_data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
            "first_name": "Alice",
            "last_name": "Smith",
            "date_of_birth": "1995-05-05",
            "role": "employee"
        }
        self.user = UserModel.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="bobpass",
            first_name="Bob",
            last_name="Builder",
            date_of_birth="1992-02-02",
            role="employee"
        )

    def test_register_user_success(self):
        url = reverse('register_user')  # Use your URL name
        response = self.client.post(url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User registered successfully")
        self.assertTrue(UserModel.objects.filter(username="alice").exists())

    def test_register_user_missing_fields(self):
        url = reverse('register_user')
        response = self.client.post(url, {"username": "incomplete"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_user_success(self):
        url = reverse('login_user')  # Use your URL name
        response = self.client.post(url, {"identifier": "bob", "password": "bobpass"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_user_invalid_credentials(self):
        url = reverse('login_user')
        response = self.client.post(url, {"identifier": "bob", "password": "wrongpass"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Invalid credentials")

    def test_login_user_missing_fields(self):
        url = reverse('login_user')
        response = self.client.post(url, {"identifier": ""}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Both identifier and password are required.")
