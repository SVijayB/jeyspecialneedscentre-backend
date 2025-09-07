from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Display fields in the admin list view
    list_display = ['username', 'employee_id', 'first_name', 'last_name', 'role', 'branch', 'is_active', 'is_verified']
    list_filter = ['role', 'branch', 'is_active', 'is_verified', 'date_joined']
    search_fields = ['username', 'employee_id', 'first_name', 'last_name', 'email']
    ordering = ['username']
    
    # Fields to display in the detail view
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'role', 'mobile_number', 'branch', 'supervisor')
        }),
        ('Work Schedule', {
            'fields': ('login_time', 'grace_time')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields to display when adding a new user
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'role', 'mobile_number', 'branch', 'supervisor')
        }),
        ('Work Schedule', {
            'fields': ('login_time', 'grace_time')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('branch', 'supervisor')
