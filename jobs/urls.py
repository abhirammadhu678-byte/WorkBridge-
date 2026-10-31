from django.urls import path
from . import views

urlpatterns = [
    path('job-application/', views.job_application, name='job_application'),
    path('job-post/', views.job_post, name='job_post'),
    path('available-jobs/', views.available_jobs, name='available_jobs'),
    path('applied-jobs/', views.applied_jobs, name='applied_jobs'),
    path('apply-job/<int:job_id>/', views.apply_job, name='apply_job'),
]