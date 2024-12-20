from django.contrib import admin
from .models import CustomUser, Skill, Project, Payment, ProjectImage

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'is_premium')  
    ordering = ('email',)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'description', )
    search_fields = ('title', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('user',)
      # Order by creation date, descending

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_id', 'status', 'created_at')
    search_fields = ('user__email', 'transaction_id')
    list_filter = ('status', 'user')
    ordering = ('-created_at',)

class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'image')
    search_fields = ('project__title',)
    list_filter = ('project',)
    ordering = ('project__title',)

# Register models with admin interface
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Skill)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)
