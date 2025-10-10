from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Task, TaskAttachment
from .serializers import TaskSerializer
from .permissions import TaskPermission
from .pagination import TaskPagination
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@api_view(['POST'])
@permission_classes([TaskPermission])
def create_task(request):
    serializer = TaskSerializer(data = request.data,
                                context = {'request': request})
    if serializer.is_valid():
        task = serializer.save()
        """
            handle file uploads
        """
        files = request.FILES.getlist('files')
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        for f in files:
            TaskAttachment.objects.create(task=task, file=f)
        
        # notification code
        channel_layer = get_channel_layer()
        for employee in task.assigned_to.all():
            async_to_sync(channel_layer.group_send)(
                f"user_{employee.id}",
                {
                    'type': 'send_notification',
                    'message': {
                        'title': 'New Task Assigned',
                        'task_id': task.id,
                        'task_title': task.title,
                        'assigned_by': request.user.username,
                    }
                }
            )
        return Response(TaskSerializer(task, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([TaskPermission])
def list_all_task(request):
    tasks = Task.objects.all().order_by('-created_at')
    paginator = TaskPagination()
    paginated_tasks = paginator.paginate_queryset(tasks, request)
    serializer = TaskSerializer(paginated_tasks, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([TaskPermission])
def list_one_task(request, task_id):
    try:
        task = Task.obejcts.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = TaskSerializer(task)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([TaskPermission])
def update_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TaskSerializer(task, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([TaskPermission])
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    task.delete()
    return Response({'message': 'Task deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['PATCH'])
@permission_classes([TaskPermission])
def mark_task_complete(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check object-level permission
    permission = TaskPermission()
    if not permission.has_object_permission(request, mark_task_complete, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Update status
    task.status = 'Completed'
    task.save()
    
    return Response({'message': 'Task marked as completed', 'task_id': task.id}, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([TaskPermission])
def update_task_deadline(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    permission = TaskPermission()
    if not permission.has_object_permission(request, update_task_deadline, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
     # Get new deadline from request
    new_deadline = request.data.get('deadline')
    if not new_deadline:
        return Response({'error': 'Deadline is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Parse the deadline string into a date object
        task.deadline = datetime.fromisoformat(new_deadline)
    except ValueError:
        return Response({'error': 'Invalid deadline format. Use ISO format: YYYY-MM-DD'}, 
                        status=status.HTTP_400_BAD_REQUEST)

    task.save()
    return Response({'message': 'Task deadline updated', 'task_id': task.id, 'new_deadline': task.deadline}, 
                    status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([TaskPermission])
def filter_by_status(request):
    status_param = request.query_params.get('status')
    if not status_param:
        return Response({
            'error': 'Status query parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if user.role == 'ADMIN':
        tasks = Task.objects.filter(status_iexact=status_param)
    
    elif user.role == 'MANAGER':
        tasks = Task.objects.filter(status_iexact=status_param, assigned_to=user)
    
    paginator = TaskPagination()
    paginated_tasks = paginator.paginate_queryset(tasks.order_by('-created_at'), request)
    serializer = TaskSerializer(paginated_tasks, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([TaskPermission])
def filter_by_deadline(request):
    return