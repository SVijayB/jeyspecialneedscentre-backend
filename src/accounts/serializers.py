"""
DRF Serializers for User and Branch management
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import Branch

User = get_user_model()


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for Branch model"""
    
    class Meta:
        model = Branch
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (lightweight)"""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'employee_id', 'username', 'first_name', 'last_name', 
                 'email', 'role', 'branch_name', 'is_active']


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user operations"""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'employee_id', 'username', 'first_name', 'last_name', 
                 'email', 'password', 'role', 'branch', 'branch_name', 
                 'mobile_number', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with optional password change"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['employee_id', 'username', 'first_name', 'last_name', 
                 'email', 'password', 'role', 'branch', 'mobile_number']
    
    def validate_employee_id(self, value):
        """Ensure employee_id is unique"""
        if User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Employee ID already exists")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_verified = True  # Auto-verify admin-created users
        user.save()
        return user
