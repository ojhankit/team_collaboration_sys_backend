from django.db import models
from django.contrib.auth.models import AbstractUser

class UserModel(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MANAGER = 'manager', 'Manager'
        EMPLOYEE = 'employee', 'Employee'

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(blank=True,null=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.EMPLOYEE)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
