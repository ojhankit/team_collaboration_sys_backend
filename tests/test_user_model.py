from django.test import TestCase
from apps.users.models import UserModel

class UserModelTest(TestCase):

    def setUp(self):
        self.user = UserModel.objects.create_user(
            username="john_doe",
            email="john@example.com",
            password="strongpassword",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            role=UserModel.Roles.EMPLOYEE
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, "john_doe")
        self.assertEqual(self.user.email, "john@example.com")
        self.assertTrue(self.user.check_password("strongpassword"))
        self.assertEqual(self.user.role, UserModel.Roles.EMPLOYEE)

    def test_user_str_and_repr(self):
        self.assertEqual(str(self.user), "john_doe (employee)")
        self.assertEqual(repr(self.user), "<User john_doe (employee)>")
