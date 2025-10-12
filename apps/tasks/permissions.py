from rest_framework.permissions import BasePermission

class TaskPermission(BasePermission):
    """
    Custom permission for Task model:
    - Admin: full access
    - Manager: can create tasks, update tasks they assigned
    - Employee: can view tasks assigned to them and update progress/status
    """

    def has_permission(self, request, view):
        user = request.user

        # Everyone must be authenticated
        if not user.is_authenticated:
            return False

        # Admin can do everything
        if user.role == 'admin':
            return True

        # Managers can create tasks
        if request.method == 'POST' and user.role == 'manager':
            return True

        # Employees cannot create tasks
        if request.method == 'POST' and user.role == 'employee':
            return False

        # For GET, PUT, PATCH, DELETE → allow and check object-level later
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin can do everything
        if user.role == 'admin':
            return True

        # Manager can update/delete tasks they assigned
        if user.role == 'manager':
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return obj.assigned_by == user
            return True  # GET is allowed

        # Employee can only view or update tasks assigned to them
        if user.role == 'employee':
            if request.method in ['PUT', 'PATCH']:
                return user in obj.assigned_to.all()
            if request.method == 'GET':
                return user in obj.assigned_to.all()
            return False  # DELETE not allowed

        # Default deny
        return False
