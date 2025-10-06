from rest_framework import serializers
from .models import Task
from apps.users.models import UserModel
from django.utils import timezone

class TaskSerializer(serializers.ModelSerializer):
    assigned_by = serializers.StringRelatedField(read_only=True)  # show username/email
    assigned_to = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UserModel.objects.filter(role='EMPLOYEE')  # only employees  # will set dynamically in view
    )
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'docs',
            'assigned_by',
            'assigned_to',
            'deadline',
            'assigned_date',
            'labels'
        ]
        read_only_fields = ['assigned_by', 'assigned_date']

    def create(self, validated_data):
        assigned_to_data = validated_data.pop('assigned_to')
        task = Task.objects.create(**validated_data, assigned_by=self.context['request'].user)
        task.assigned_to.set(assigned_to_data)
        return task
