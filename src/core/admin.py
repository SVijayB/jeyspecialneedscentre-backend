from django.contrib import admin
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'active_users_count', 'therapists_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['active_users_count', 'therapists_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Branch Information', {
            'fields': ('name',)
        }),
        ('Statistics', {
            'fields': ('active_users_count', 'therapists_count'),
            'classes': ('collapse',)
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
