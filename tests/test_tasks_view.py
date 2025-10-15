from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.tasks.models import Task, TaskAttachment
from datetime import date, timedelta
import io
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class TaskAPITestCase(TestCase):
    def setUp(self):
        # Create users for roles
        self.admin_user = User.objects.create_user(username="admin", password="Admin123@", role="admin")
        self.manager_user = User.objects.create_user(username="manager", password="Manager123@", role="manager")
        self.employee_user = User.objects.create_user(username="employee", password="Employee123@", role="employee")
        
        # API client
        self.client = APIClient()

        # Sample task data
        self.task_data = {
            "title": "Test Task",
            "description": "Task description",
            "deadline": str(date.today() + timedelta(days=7)),
            "assigned_to": [self.employee_user.id],
            "labels": "test,unit"
        }

    def authenticate(self, user):
        """Helper function to login user and set token"""
        response = self.client.post("/api/login/", {"identifier": user.username, "password": user.username.capitalize() + "123@"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_task_as_admin(self):
        self.authenticate(self.admin_user)
        # Include file attachment
        file_obj = SimpleUploadedFile("test.txt", b"Hello World")
        data = self.task_data.copy()
        data['files'] = [file_obj]

        response = self.client.post("/api/tasks/create/", data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(TaskAttachment.objects.count(), 1)
        self.assertEqual(response.data['title'], "Test Task")

    def test_create_task_as_employee_denied(self):
        self.authenticate(self.employee_user)
        response = self.client.post("/api/tasks/create/", self.task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_tasks(self):
        self.authenticate(self.admin_user)
        Task.objects.create(title="Task1", description="Desc", deadline=date.today(), assigned_by=self.admin_user)
        Task.objects.create(title="Task2", description="Desc", deadline=date.today(), assigned_by=self.admin_user)
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_update_task_partial(self):
        self.authenticate(self.manager_user)
        task = Task.objects.create(title="Old Task", description="Desc", deadline=date.today(), assigned_by=self.manager_user)
        response = self.client.patch(f"/api/tasks/{task.id}/update/", {"title": "Updated Task"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, "Updated Task")

    def test_delete_task(self):
        self.authenticate(self.admin_user)
        task = Task.objects.create(title="Delete Task", description="Desc", deadline=date.today(), assigned_by=self.admin_user)
        response = self.client.delete(f"/api/tasks/{task.id}/delete/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_mark_task_complete(self):
        self.authenticate(self.manager_user)
        task = Task.objects.create(title="Complete Task", description="Desc", deadline=date.today(), assigned_by=self.manager_user)
        task.assigned_to.add(self.employee_user)
        response = self.client.patch(f"/api/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "Completed")

    def test_filter_by_status(self):
        self.authenticate(self.admin_user)
        Task.objects.create(title="Pending Task", description="Desc", deadline=date.today(), status="pending", assigned_by=self.admin_user)
        Task.objects.create(title="Completed Task", description="Desc", deadline=date.today(), status="completed", assigned_by=self.admin_user)
        response = self.client.get("/api/tasks/filter-status/?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], "pending")

    def test_filter_by_deadline(self):
        self.authenticate(self.admin_user)
        Task.objects.create(title="Task1", description="Desc", deadline=date.today() + timedelta(days=2), assigned_by=self.admin_user)
        Task.objects.create(title="Task2", description="Desc", deadline=date.today() + timedelta(days=10), assigned_by=self.admin_user)
        filter_date = str(date.today() + timedelta(days=5))
        response = self.client.get(f"/api/tasks/filter-deadline/?date={filter_date}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertLessEqual(response.data['results'][0]['deadline'], filter_date)
