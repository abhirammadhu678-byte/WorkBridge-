from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'location', 'work_date', 'work_duration', 'created_at')
    search_fields = ('job_title', 'location', 'required_skills')
    list_filter = ('work_duration', 'work_date')
