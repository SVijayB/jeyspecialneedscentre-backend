from django.contrib import admin
from django.db.models import Count, Q
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_active_users_count', 'get_therapists_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with annotations to avoid N+1 queries"""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_users=Count('users'),
            total_therapists=Count('users', filter=Q(users__role='therapist'))
        )
    
    def get_active_users_count(self, obj):
        """Display annotated active users count"""
        return obj.total_users
    get_active_users_count.short_description = 'Active Users'
    get_active_users_count.admin_order_field = 'total_users'
    
    def get_therapists_count(self, obj):
        """Display annotated therapists count"""
        return obj.total_therapists
    get_therapists_count.short_description = 'Therapists'
    get_therapists_count.admin_order_field = 'total_therapists'

    fieldsets = (
        ('Branch Information', {
            'fields': ('name',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add help text for the name field
        if 'name' in form.base_fields:
            form.base_fields['name'].help_text = "Enter branch name (e.g., Chennai, Bengaluru, Mumbai, Pune, etc.)"
        return form
