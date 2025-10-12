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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new task",
    operation_description="""
    Creates a new task and assigns it to one or more employees.
    
    **Features:**
    - Supports file attachments (multiple files)
    - Supports document URL linking
    - Automatically sets assigned_by to current user
    - Automatically sets assigned_date to current timestamp
    - Sends real-time notifications to assigned employees via WebSocket
    - Supports comma-separated labels for task categorization
    
    **Access Control:**
    Requires admin or manager role
    
    **File Upload:**
    Use multipart/form-data with 'files' field for attachments.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['title', 'description', 'deadline', 'assigned_to'],
        properties={
            'title': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Task title (max 255 characters)",
                example="Complete project documentation"
            ),
            'description': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Detailed task description",
                example="Write comprehensive documentation for the API endpoints including examples and use cases"
            ),
            'docs': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_URI,
                description="Optional: URL to external documentation or resources",
                example="https://docs.google.com/document/d/abc123"
            ),
            'deadline': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="Task deadline in YYYY-MM-DD format",
                example="2025-12-31"
            ),
            'assigned_to': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description="List of user IDs to assign the task to",
                example=[1, 2, 3]
            ),
            'labels': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Optional: Comma-separated labels for categorization",
                example="urgent,backend,api"
            ),
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['pending', 'in_progress', 'completed'],
                description="Task status (defaults to 'pending')",
                example="pending"
            ),
            'files': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_FILE),
                description="Optional file attachments (use multipart/form-data)",
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description="Task created successfully",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "Complete project documentation",
                    "description": "Write comprehensive documentation for the API endpoints",
                    "docs": "https://docs.google.com/document/d/abc123",
                    "status": "pending",
                    "deadline": "2025-12-31",
                    "assigned_date": "2025-10-12T10:30:00Z",
                    "assigned_by": {
                        "id": 5,
                        "username": "manager_user"
                    },
                    "assigned_to": [1, 2, 3],
                    "labels": "urgent,backend,api",
                    "attachments": []
                }
            }
        ),
        400: openapi.Response(
            description="Validation error",
            examples={
                "application/json": {
                    "title": ["This field is required."],
                    "deadline": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
                }
            }
        ),
        403: openapi.Response(
            description="Permission denied - requires admin or manager role",
            examples={
                "application/json": {
                    "detail": "You do not have permission to perform this action."
                }
            }
        )
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
@api_view(['POST'])
@permission_classes([TaskPermission])
def create_task(request):
    serializer = TaskSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        task = serializer.save()
        
        # Handle file uploads
        files = request.FILES.getlist('files')
        for f in files:
            TaskAttachment.objects.create(task=task, file=f)
        
        # Send real-time notifications to assigned employees
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
        return Response(
            TaskSerializer(task, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_summary="List all tasks",
    operation_description="""
    Retrieves a paginated list of all tasks ordered by assigned date (newest first).
    
    **Access Control:**
    - Admins: See all tasks in the system
    - Managers: See tasks assigned to them or created by them
    - Employees: See only tasks assigned to them
    
    **Response includes:**
    - Task details (title, description, status, labels)
    - Assigned by and assigned to user information
    - Deadline and assigned date
    - File attachments list
    - Document URL if available
    
    **Pagination:**
    Results are paginated. Use 'page' and 'page_size' query parameters.
    """,
    manual_parameters=[
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size',
            openapi.IN_QUERY,
            description="Number of items per page (default: 10)",
            type=openapi.TYPE_INTEGER,
            default=10
        ),
    ],
    responses={
        200: openapi.Response(
            description="Paginated list of tasks",
            examples={
                "application/json": {
                    "count": 50,
                    "next": "http://api.example.com/tasks/?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "Complete project documentation",
                            "description": "Write comprehensive API docs",
                            "status": "pending",
                            "deadline": "2025-12-31",
                            "assigned_date": "2025-10-12T10:30:00Z",
                            "labels": "urgent,backend",
                            "docs": "https://docs.google.com/document/d/abc",
                            "assigned_by": {"id": 5, "username": "manager"},
                            "assigned_to": [1, 2, 3]
                        }
                    ]
                }
            }
        ),
        403: openapi.Response(
            description="Permission denied",
            examples={
                "application/json": {
                    "detail": "You do not have permission to perform this action."
                }
            }
        )
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
@api_view(['GET'])
@permission_classes([TaskPermission])
def list_all_task(request):
    tasks = Task.objects.all().order_by('-assigned_date')
    paginator = TaskPagination()
    paginated_tasks = paginator.paginate_queryset(tasks, request)
    serializer = TaskSerializer(paginated_tasks, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_summary="Get a single task by ID",
    operation_description="""
    Retrieves detailed information about a specific task.
    
    **Response includes:**
    - All task fields (title, description, status, labels, docs)
    - Complete user details for assigned_by
    - List of assigned users
    - All file attachments with URLs
    - Timestamps (assigned_date, attachment upload times)
    
    **Access Control:**
    Users can only view tasks they have access to based on their role.
    """,
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_PATH,
            description="Unique task identifier",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    responses={
        200: openapi.Response(
            description="Task details retrieved successfully",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "Complete project documentation",
                    "description": "Write comprehensive documentation for the API endpoints",
                    "docs": "https://docs.google.com/document/d/abc123",
                    "status": "pending",
                    "deadline": "2025-12-31",
                    "assigned_date": "2025-10-12T10:30:00Z",
                    "labels": "urgent,backend,api",
                    "assigned_by": {
                        "id": 5,
                        "username": "manager_user",
                        "email": "manager@example.com"
                    },
                    "assigned_to": [
                        {"id": 1, "username": "employee1"},
                        {"id": 2, "username": "employee2"}
                    ],
                    "attachments": [
                        {
                            "id": 1,
                            "file": "/media/task_files/document.pdf",
                            "uploaded_at": "2025-10-12T10:35:00Z"
                        }
                    ]
                }
            }
        ),
        404: openapi.Response(
            description="Task not found",
            examples={
                "application/json": {
                    "error": "Task not found"
                }
            }
        ),
        403: "Permission denied"
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
@api_view(['GET'])
@permission_classes([TaskPermission])
def list_one_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = TaskSerializer(task, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='put',
    operation_summary="Update task (full update)",
    operation_description="""
    Updates all fields of an existing task. All required fields must be provided.
    
    **Note:** 
    - assigned_by cannot be changed (automatically set by system)
    - assigned_date cannot be changed (timestamp of original creation)
    - Use PATCH for partial updates
    """,
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_PATH,
            description="Task ID to update",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['title', 'description', 'deadline', 'assigned_to'],
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description="Task title"),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description="Task description"),
            'docs': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_URI,
                description="Optional document URL"
            ),
            'deadline': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATE,
                description="Deadline (YYYY-MM-DD)"
            ),
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['pending', 'in_progress', 'completed'],
                description="Task status"
            ),
            'assigned_to': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description="List of user IDs"
            ),
            'labels': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Comma-separated labels"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Task updated successfully",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "Updated task title",
                    "status": "in_progress",
                    "labels": "urgent,updated"
                }
            }
        ),
        400: "Validation error",
        404: "Task not found",
        403: "Permission denied"
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
@swagger_auto_schema(
    method='patch',
    operation_summary="Update task (partial update)",
    operation_description="""
    Updates specific fields of an existing task. Only provided fields will be updated.
    
    **Updateable fields:**
    - title, description, docs
    - status (pending, in_progress, completed)
    - deadline
    - assigned_to (list of user IDs)
    - labels (comma-separated string)
    
    **Access Control:**
    - Admins: Can update any task
    - Managers: Can update tasks they created or are assigned to
    - Employees: Can update status of tasks assigned to them
    
    **Note:** assigned_by and assigned_date are immutable
    """,
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_PATH,
            description="Task ID to update",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description="Optional: Update task title"),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description="Optional: Update description"),
            'docs': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_URI,
                description="Optional: Update document URL"
            ),
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['pending', 'in_progress', 'completed'],
                description="Optional: Update status"
            ),
            'deadline': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="Optional: Update deadline (YYYY-MM-DD)"
            ),
            'assigned_to': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description="Optional: Update assigned users"
            ),
            'labels': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Optional: Update labels (comma-separated)"
            ),
        }
    ),
    responses={
        200: "Task updated successfully",
        400: "Validation error",
        404: "Task not found",
        403: "Permission denied"
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
@api_view(['PUT', 'PATCH'])
@permission_classes([TaskPermission])
def update_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = TaskSerializer(
        task,
        data=request.data,
        partial=partial,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a task",
    operation_description="""
    Permanently deletes a task and all associated data.
    
    **Cascade deletion includes:**
    - All file attachments (TaskAttachment records and files)
    - All related records
    
    **Access Control:**
    - Admins: Can delete any task
    - Managers: Can delete tasks they created (assigned_by = current user)
    - Employees: Cannot delete tasks
    
    **⚠️ Warning:** This action cannot be undone. All data will be permanently lost.
    """,
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_PATH,
            description="Task ID to delete",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    responses={
        204: openapi.Response(
            description="Task deleted successfully (no content returned)",
            examples={
                "application/json": {
                    "message": "Task deleted successfully"
                }
            }
        ),
        404: openapi.Response(
            description="Task not found",
            examples={
                "application/json": {
                    "error": "Task not found"
                }
            }
        ),
        403: "Permission denied - insufficient privileges"
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
@api_view(['DELETE'])
@permission_classes([TaskPermission])
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    task.delete()
    return Response({'message': 'Task deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='patch',
    operation_summary="Mark task as completed",
    operation_description="""
    Changes the task status to 'completed'.
    
    **Behavior:**
    - Updates status field to 'completed'
    - Does not change any other fields
    - Useful for quick status updates without full PATCH request
    
    **Access Control:**
    - Admins: Can mark any task as completed
    - Managers: Can mark tasks they manage as completed
    - Employees: Can mark tasks assigned to them as completed
    """,
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_PATH,
            description="Task ID to mark as completed",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    responses={
        200: openapi.Response(
            description="Task marked as completed",
            examples={
                "application/json": {
                    "message": "Task marked as completed",
                    "task_id": 1
                }
            }
        ),
        404: "Task not found",
        403: openapi.Response(
            description="Permission denied",
            examples={
                "application/json": {
                    "error": "Permission denied"
                }
            }
        )
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
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

    # Update status to completed
    task.status = Task.Status.COMPLETED
    task.save()
    
    return Response(
        {'message': 'Task marked as completed', 'task_id': task.id},
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='patch',
    operation_summary="Update task deadline",
    operation_description="""
    Updates only the deadline field for a specific task.
    
    **Use Case:**
    Quick deadline extension/update without modifying other fields.
    
    **Access Control:**
    - Admins: Can update any task deadline
    - Managers: Can update deadlines for tasks they created (assigned_by = current user)
    - Employees: Cannot update deadlines
    """,
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_PATH,
            description="Task ID",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['deadline'],
        properties={
            'deadline': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="New deadline in YYYY-MM-DD format",
                example="2025-12-31"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Deadline updated successfully",
            examples={
                "application/json": {
                    "message": "Task deadline updated",
                    "task_id": 1,
                    "new_deadline": "2025-12-31"
                }
            }
        ),
        400: openapi.Response(
            description="Invalid request - missing or invalid deadline",
            examples={
                "application/json": {
                    "error": "Invalid deadline format. Use ISO format: YYYY-MM-DD"
                }
            }
        ),
        404: "Task not found",
        403: "Permission denied"
    },
    security=[{'Bearer': []}],
    tags=['Tasks']
)
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
        return Response(
            {'error': 'Invalid deadline format. Use ISO format: YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )

    task.save()
    return Response(
        {
            'message': 'Task deadline updated',
            'task_id': task.id,
            'new_deadline': str(task.deadline)
        },
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='get',
    operation_summary="Filter tasks by status",
    operation_description="""
    Retrieves tasks filtered by their status.
    
    **Available Status Values:**
    - `pending` - Task not yet started
    - `in_progress` - Task currently being worked on
    - `completed` - Task finished
    
    **Query is case-insensitive:** 'Pending', 'pending', 'PENDING' all work
    
    **Access Control:**
    - Admins: See all tasks with the specified status
    - Managers/Employees: See only tasks assigned to them with the specified status
    
    **Pagination:**
    Results are paginated and ordered by assigned_date (newest first).
    """,
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Task status to filter by (case-insensitive)",
            type=openapi.TYPE_STRING,
            required=True,
            enum=['pending', 'in_progress', 'completed'],
            example="pending"
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size',
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=10
        ),
    ],
    responses={
        200: openapi.Response(
            description="Filtered tasks",
            examples={
                "application/json": {
                    "count": 15,
                    "next": "http://api.example.com/tasks/filter-status/?status=pending&page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "Complete documentation",
                            "status": "pending",
                            "deadline": "2025-12-31",
                            "labels": "urgent,backend"
                        }
                    ]
                }
            }
        ),
        400: openapi.Response(
            description="Missing status parameter",
            examples={
                "application/json": {
                    "error": "Status query parameter is required"
                }
            }
        )
    },
    security=[{'Bearer': []}],
    tags=['Tasks', 'Filters']
)
@api_view(['GET'])
@permission_classes([TaskPermission])
def filter_by_status(request):
    status_param = request.query_params.get('status')
    if not status_param:
        return Response(
            {'error': 'Status query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user
    if user.role == 'ADMIN':
        tasks = Task.objects.filter(status__iexact=status_param)
    elif user.role == 'MANAGER':
        tasks = Task.objects.filter(status__iexact=status_param, assigned_to=user)
    else:  # Employee
        tasks = Task.objects.filter(status__iexact=status_param, assigned_to=user)
    
    paginator = TaskPagination()
    paginated_tasks = paginator.paginate_queryset(tasks.order_by('-assigned_date'), request)
    serializer = TaskSerializer(paginated_tasks, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_summary="Filter tasks by deadline",
    operation_description="""
    Retrieves tasks with deadlines on or before the specified date.
    
    **Use Cases:**
    - Find overdue tasks: Use today's date
    - Find tasks due this week: Use date 7 days from now
    - Find tasks due this month: Use end of month date
    
    **Query Logic:**
    Returns tasks where `deadline <= provided_date`
    
    **Access Control:**
    - Admins: See all tasks matching the deadline criteria
    - Managers/Employees: See only their assigned tasks matching the criteria
    
    **Pagination:**
    Results are paginated and ordered by deadline (earliest/most urgent first).
    """,
    manual_parameters=[
        openapi.Parameter(
            'date',
            openapi.IN_QUERY,
            description="Filter tasks with deadline on or before this date (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
            required=True,
            example="2025-12-31"
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size',
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=10
        ),
    ],
    responses={
        200: openapi.Response(
            description="Tasks filtered by deadline",
            examples={
                "application/json": {
                    "count": 8,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "Urgent task",
                            "deadline": "2025-10-15",
                            "status": "pending",
                            "labels": "urgent"
                        }
                    ]
                }
            }
        ),
        400: openapi.Response(
            description="Missing or invalid date parameter",
            examples={
                "application/json": {
                    "error": "Invalid date format, Use YYYY-MM-DD"
                }
            }
        )
    },
    security=[{'Bearer': []}],
    tags=['Tasks', 'Filters']
)
@api_view(['GET'])
@permission_classes([TaskPermission])
def filter_by_deadline(request):
    deadline_str = request.query_params.get("date")
    if not deadline_str:
        return Response(
            {"error": "Please provide a 'date' query parameter in YYYY-MM-DD format."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return Response(
            {"error": "Invalid date format, Use YYYY-MM-DD"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user
    if user.role == 'ADMIN':
        tasks = Task.objects.filter(deadline__lte=deadline)
    else:
        tasks = Task.objects.filter(deadline__lte=deadline, assigned_to=user)

    paginator = TaskPagination()
    paginated_tasks = paginator.paginate_queryset