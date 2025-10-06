from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Task
from .serializers import TaskSerializer
from .permissions import TaskPermission


@api_view(['POST'])
@permission_classes([TaskPermission])
def create_task(request):
    serializer = TaskSerializer(data = request.data,
                                context = {'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([TaskPermission])
def list_all_task(request):
    tasks = Task.objects.all()
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([TaskPermission])
def list_one_task(request, task_id):
    try:
        tasks = Task.obejcts.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = TaskSerializer(tasks)
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