from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_all_task, name='task-list'),
    path('create/', views.create_task, name='task-create'),
    path('<int:task_id>/', views.list_one_task, name='task-detail'),
    path('<int:task_id>/update/', views.update_task, name='task-update'),
    path('<int:task_id>/delete/', views.delete_task, name='task-delete'),
    path('<int:task_id>/complete/', views.mark_task_complete, name='mark_task_complete'),
    path('<int:task_id>/deadline/', views.update_task_deadline, name='update_task_deadline'),
    path('filter/status/', views.filter_by_status, name='filter_by_status'),
    path('filter-by-deadline/', views.filter_by_deadline, name='filter-by-deadline'),
]
