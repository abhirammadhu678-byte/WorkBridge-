from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('job-post/', views.job_post, name='job_post'),
    path('register/', views.customer_register, name='customer_register'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('applicants-for-job/<int:job_id>/', views.applicants_for_job, name='applicants_for_job'),
    path('job-edit/<int:job_id>/', views.job_edit, name='job_edit'),
    path('job-delete/<int:job_id>/', views.job_delete, name='job_delete'),
    path('applicant-selection/', views.applicant_selection, name='applicant_selection'),
    path('applicant-selection/<int:application_id>/', views.applicant_selection, name='applicant_selection'),
    path('work-completion/', views.work_completion, name='work_completion'),
    path('work-completion/<int:application_id>/', views.work_completion, name='work_completion'),
    path('rating-review/', views.rating_review, name='rating_review'),
    path('rating-review/<int:application_id>/', views.rating_review, name='rating_review'),
    path('manage-application/<int:application_id>/<str:action>/', views.manage_application, name='manage_application'),
]