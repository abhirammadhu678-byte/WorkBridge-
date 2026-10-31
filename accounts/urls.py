from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student-register/', views.student_register, name='student_register'),
    path('student-verification/', views.student_verification, name='student_verification'),
    path('student-profile/', views.student_profile, name='student_profile'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('delete-portfolio/<int:portfolio_id>/', views.delete_portfolio, name='delete_portfolio'),

    # Admin Portal Routes
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/verifications/', views.admin_verifications, name='admin_verifications'),
    path('admin-dashboard/verifications/approve/<int:student_id>/', views.approve_student, name='approve_student_verification'),
    path('admin-dashboard/verifications/reject/<int:student_id>/', views.reject_student, name='reject_student_verification'),
    path('approve-student/<int:student_id>/', views.approve_student, name='approve_student'),
    path('reject-student/<int:student_id>/', views.reject_student, name='reject_student'),

    # User Management
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin-dashboard/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin-dashboard/users/<int:user_id>/toggle-status/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
    path('admin-dashboard/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),

    # Job Management
    path('admin-dashboard/jobs/', views.admin_jobs, name='admin_jobs'),
    path('admin-dashboard/jobs/<int:job_id>/edit/', views.admin_job_edit, name='admin_job_edit'),
    path('admin-dashboard/jobs/<int:job_id>/delete/', views.admin_job_delete, name='admin_job_delete'),

    # Application Management
    path('admin-dashboard/applications/', views.admin_applications, name='admin_applications'),
    path('admin-dashboard/applications/<int:app_id>/status/', views.admin_application_status, name='admin_application_status'),
    path('admin-dashboard/applications/<int:app_id>/delete/', views.admin_application_delete, name='admin_application_delete'),

    # Report & Moderation Management
    path('admin-dashboard/reports/', views.admin_reports, name='admin_reports'),
    path('admin-dashboard/reports/<int:report_id>/resolve/', views.admin_resolve_report, name='admin_resolve_report'),
    path('report/create/', views.create_report, name='create_report'),
]