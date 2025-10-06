from rest_framework.serializers import ModelSerializer
from .models import UserModel

class UserSerializer(ModelSerializer):
    class Meta:
        model = UserModel
        fields = [          
            'email',
            'password',
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth'
        ]
        extra_kwargs = {
            'password': {'write_only': True},  
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = UserModel(**validated_data)
        user.set_password(password)
        user.save()
        return user