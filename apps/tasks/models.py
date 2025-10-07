from django.db import models
from django.conf import settings
from django.utils import timezone
"""
Task Model 
1. task_title
2. task_description
3. task_doc // optional
4. assigned_by // one to one with users
5. assigned_to // one to many with users
6. deadline
7. assigned_date // curr date
8. labels // multiple labels
"""

class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In_Progress'
        COMPLETED = 'completed', 'Completed'

    title = models.CharField(max_length=255)
    description = models.TextField()
    docs = models.URLField(blank=True, null=True)  # optional
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks_assigned'
    )
    assigned_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='tasks_received'
    )
    deadline = models.DateField()
    assigned_date = models.DateTimeField(default=timezone.now)
    labels = models.CharField(max_length=255, blank=True)  # comma-separated labels
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Task: {self.title} assigned_by={self.assigned_by.username}>"


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
