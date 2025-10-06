from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_all_task, name='task-list'),
    path('create/', views.create_task, name='task-create'),
    path('<int:task_id>/', views.list_one_task, name='task-detail'),
    path('<int:task_id>/update/', views.update_task, name='task-update'),
    path('<int:task_id>/delete/', views.delete_task, name='task-delete'),
]
