from django.contrib import admin
from .models import Task, TaskAttachment
# Register your models here.

admin.site.register(Task)
admin.site.register(TaskAttachment)