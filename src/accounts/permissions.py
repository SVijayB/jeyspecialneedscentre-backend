"""
Custom permissions for role-based access control
"""

from rest_framework.permissions import BasePermission


class IsSuperAdminOrHR(BasePermission):
    """
    Permission for superadmin and HR users only
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['superadmin', 'hr']
        )


class IsSuperAdminOnly(BasePermission):
    """
    Permission for superadmin users only
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'superadmin'
        )


class IsOwnerOrSuperAdminOrHR(BasePermission):
    """
    Permission for object owner, superadmin, or HR
    HR can only access users in their branch
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superadmin has access to everything
        if user.role == 'superadmin':
            return True
        
        # HR can access users in their branch
        if user.role == 'hr':
            return obj.branch == user.branch
        
        # Users can only access their own data
        return obj == user


class BranchBasedPermission(BasePermission):
    """
    Permission that restricts access based on user's branch
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superadmin has access to everything
        if user.role == 'superadmin':
            return True
        
        # HR and supervisors can access data from their branch
        if user.role in ['hr', 'supervisor']:
            if hasattr(obj, 'branch'):
                return obj.branch == user.branch
            elif hasattr(obj, 'employee') and hasattr(obj.employee, 'branch'):
                return obj.employee.branch == user.branch
        
        # Therapists can only access their own data
        if user.role == 'therapist':
            if hasattr(obj, 'employee'):
                return obj.employee == user
            return obj == user
        
        return False
