from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q, Avg, Count
from django.urls import reverse

from .models import CustomUser, Portfolio, Place, Report, KERALA_DISTRICTS
from .forms import (
    StudentRegistrationForm,
    StudentVerificationForm,
    StudentProfileForm,
    PortfolioForm,
    AdminUserCreationForm,
    AdminUserEditForm,
    AdminJobEditForm,
    ReportCreationForm,
    ReportResolutionForm,
)
from jobs.models import Job, JobApplication
from customers.models import Customer, Review, WorkCompletion
from students.models import Student, Notification



def home_view(request):
    return render(request, 'home.html')


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@login_required
def student_dashboard(request):
    if request.user.user_type != 'student' and not (request.user.is_staff or request.user.is_superuser):
        if request.user.user_type == 'customer':
            return redirect('customer_dashboard')
        return redirect('admin_dashboard')

    student_profile, _ = Student.objects.get_or_create(user=request.user)

    # Applications
    applications = JobApplication.objects.filter(
        student=request.user
    ).select_related('job', 'job__customer').order_by('-applied_at')

    total_applications = applications.count()
    pending_count = applications.filter(status='Pending').count()
    active_count = applications.filter(status__in=['Shortlisted', 'Accepted']).count()
    completed_count = applications.filter(status='Completed').count()

    # Portfolio items
    portfolios = Portfolio.objects.filter(student=student_profile).order_by('-uploaded_at')
    portfolio_count = portfolios.count()

    # Recommended Jobs (Prioritizing upcoming openings matching skills or latest openings)
    import datetime
    today = datetime.date.today()
    applied_job_ids = list(applications.values_list('job_id', flat=True))
    available_jobs_qs = Job.objects.exclude(id__in=applied_job_ids)

    # Filter for upcoming jobs first
    upcoming_jobs_qs = available_jobs_qs.filter(work_date__gte=today)
    pool_qs = upcoming_jobs_qs if upcoming_jobs_qs.exists() else available_jobs_qs

    skills_list = [s.strip() for s in student_profile.skills.split(',') if s.strip()] if student_profile.skills else []
    if skills_list:
        skills_q = Q()
        for skill in skills_list:
            skills_q |= Q(required_skills__icontains=skill) | Q(job_title__icontains=skill)
        recommended_jobs = pool_qs.filter(skills_q).order_by('work_date', '-created_at')[:4]
        if not recommended_jobs.exists():
            recommended_jobs = pool_qs.order_by('work_date', '-created_at')[:4]
    else:
        recommended_jobs = pool_qs.order_by('work_date', '-created_at')[:4]

    # Calculate profile strength percentage
    strength_factors = [
        bool(student_profile.full_name),
        bool(student_profile.mobile),
        bool(student_profile.college),
        bool(student_profile.profile_photo),
        bool(student_profile.skills),
        bool(student_profile.resume),
        bool(student_profile.about_me),
        bool(student_profile.college_id),
        student_profile.is_verified,
        portfolio_count > 0,
    ]
    completed_factors = sum(1 for f in strength_factors if f)
    profile_strength = int((completed_factors / len(strength_factors)) * 100)

    return render(
        request,
        'accounts/student_dashboard.html',
        {
            'student_profile': student_profile,
            'total_applications': total_applications,
            'pending_count': pending_count,
            'active_count': active_count,
            'completed_count': completed_count,
            'recent_applications': applications[:5],
            'recommended_jobs': recommended_jobs,
            'portfolios': portfolios[:4],
            'portfolio_count': portfolio_count,
            'profile_strength': profile_strength,
            'skills_list': skills_list,
        }
    )


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.user_type == 'student' and hasattr(user, 'student_profile'):
                profile = user.student_profile
                if not profile.is_verified:
                    if profile.college_id and not profile.is_rejected:
                        messages.warning(request, 'Your registration request is pending admin approval. You can log in once approved.')
                        return render(request, 'accounts/students_login.html')

            login(request, user)
            messages.success(request, 'Logged in successfully!')

            if user.is_superuser or user.is_staff or user.user_type == 'admin':
                return redirect('admin_dashboard')
            if user.user_type == 'customer':
                return redirect('customer_dashboard')
            return redirect('student_dashboard')

        messages.error(request, 'Login failed. Please check your username and password.')

    return render(request, 'accounts/students_login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def student_register(request):
    if request.user.is_authenticated:
        logout(request)

    if request.method == "POST":
        form = StudentRegistrationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                user_type='student'
            )
            student = form.save(commit=False)
            student.user = user
            student.full_name = form.cleaned_data['fullname']
            if 'place_obj' in form.cleaned_data:
                student.place = form.cleaned_data['place_obj']
            student.save()

            login(request, user)
            messages.success(request, "Account created successfully! Please submit your college ID for verification.")
            return redirect('student_verification')

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        'accounts/student_register.html',
        {
            'form': form
        }
    )


@login_required
def student_verification(request):
    if request.user.user_type != 'student':
        messages.error(request, "Only students can submit verification requests.")
        return redirect('home')

    student_profile, _ = Student.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = StudentVerificationForm(request.POST, request.FILES, instance=student_profile)

        if form.is_valid():
            student = form.save(commit=False)
            student.full_name = request.POST.get('student_name', student.full_name).strip()
            student.college = request.POST.get('college_name', student.college).strip()
            student.is_rejected = False
            student.save()
            logout(request)
            messages.success(request, "Verification documents submitted successfully! Your request is pending admin approval. You will be able to log in once verified.")
            return redirect('login')

    else:
        form = StudentVerificationForm(instance=student_profile)

    return render(
        request,
        'accounts/student_verification.html',
        {
            'form': form,
            'student_profile': student_profile
        }
    )


# =========================================================
# STUDENT PROFILE (VIEW & EDIT)
# =========================================================

@login_required
def student_profile(request):
    if request.user.user_type != 'student' and not (request.user.is_staff or request.user.is_superuser):
        return redirect('home')

    student_profile, _ = Student.objects.get_or_create(user=request.user)
    active_tab = request.GET.get('tab', 'overview')

    if request.method == "POST":
        form = StudentProfileForm(
            request.POST,
            request.FILES,
            instance=student_profile
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('student_profile')
        else:
            active_tab = 'edit'
            messages.error(request, "Please correct the errors highlighted in the profile form.")
    else:
        form = StudentProfileForm(instance=student_profile)

    skills_list = [s.strip() for s in student_profile.skills.split(',') if s.strip()] if student_profile.skills else []

    # Completed jobs and reviews count
    completed_reviews = student_profile.user.received_reviews.all()
    avg_rating = completed_reviews.aggregate(avg=Avg('rating'))['avg']
    portfolio_count = student_profile.portfolios.count()
    applied_count = JobApplication.objects.filter(student=request.user).count()

    return render(
        request,
        'accounts/student_profile.html',
        {
            'form': form,
            'student_profile': student_profile,
            'skills_list': skills_list,
            'portfolio_count': portfolio_count,
            'applied_count': applied_count,
            'reviews': completed_reviews,
            'active_tab': active_tab,
        }
    )


# =========================================================
# PORTFOLIO (VIEW, UPLOAD & DELETE)
# =========================================================

@login_required
def portfolio(request):
    if request.user.user_type != 'student' and not (request.user.is_staff or request.user.is_superuser):
        return redirect('home')

    student_profile, _ = Student.objects.get_or_create(user=request.user)
    portfolios = Portfolio.objects.filter(student=student_profile).order_by('-uploaded_at')

    if request.method == "POST":
        form = PortfolioForm(
            request.POST,
            request.FILES
        )
        if form.is_valid():
            portfolio_item = form.save(commit=False)
            portfolio_item.student = student_profile
            portfolio_item.save()
            messages.success(request, f"Portfolio project '{portfolio_item.work_title}' uploaded successfully!")
            return redirect('portfolio')
        else:
            messages.error(request, "Please check the uploaded files and form fields.")
    else:
        form = PortfolioForm()

    return render(
        request,
        'accounts/portfolio.html',
        {
            'form': form,
            'portfolios': portfolios,
            'student_profile': student_profile
        }
    )


@login_required
def delete_portfolio(request, portfolio_id):
    student_profile = get_object_or_404(Student, user=request.user)
    portfolio_item = get_object_or_404(Portfolio, id=portfolio_id, student=student_profile)
    title = portfolio_item.work_title
    portfolio_item.delete()
    messages.success(request, f"Portfolio item '{title}' deleted successfully.")
    return redirect('portfolio')


# =========================================================
# ADMIN PORTAL - DASHBOARD & MANAGEMENT VIEWS
# =========================================================

def is_admin_user(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.user_type == 'admin')


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Main administrative dashboard with KPIs, analytics, and overview."""
    students_qs = Student.objects.all()
    customers_qs = CustomUser.objects.filter(user_type='customer')
    jobs_qs = Job.objects.all()
    applications_qs = JobApplication.objects.all()
    reports_qs = Report.objects.all()

    # User metrics
    total_students = students_qs.count()
    total_customers = customers_qs.count()
    total_admins = CustomUser.objects.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(user_type='admin')).distinct().count()
    total_users = CustomUser.objects.count()

    # Verification metrics
    pending_verifications_qs = students_qs.filter(
        is_verified=False,
        is_rejected=False
    ).exclude(college_id__in=['', None]).select_related('user', 'place')
    
    pending_verifications_count = pending_verifications_qs.count()
    rejected_verifications_count = students_qs.filter(is_rejected=True).count()
    verified_students_count = students_qs.filter(is_verified=True).count()

    # Job & Application metrics
    total_jobs = jobs_qs.count()
    total_applications = applications_qs.count()
    pending_apps = applications_qs.filter(status='Pending').count()
    accepted_apps = applications_qs.filter(status='Accepted').count()
    completed_apps = applications_qs.filter(status='Completed').count()
    rejected_apps = applications_qs.filter(status='Rejected').count()

    # Moderation metrics
    pending_reports_count = reports_qs.filter(status='Pending').count()
    total_reports_count = reports_qs.count()

    # Recent Data Streams
    recent_verifications = pending_verifications_qs.order_by('-id')[:6]
    recent_jobs = jobs_qs.select_related('customer').annotate(
        applicant_count=Count('applications')
    ).order_by('-created_at')[:5]
    recent_applications = applications_qs.select_related(
        'student', 'student__student_profile', 'job', 'job__customer'
    ).order_by('-applied_at')[:6]
    recent_reports = reports_qs.select_related(
        'reporter', 'reported_user', 'reported_job'
    ).order_by('-created_at')[:5]

    context = {
        "total_users": total_users,
        "total_students": total_students,
        "total_customers": total_customers,
        "total_admins": total_admins,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "pending_verifications_count": pending_verifications_count,
        "rejected_verifications_count": rejected_verifications_count,
        "verified_students_count": verified_students_count,
        "pending_apps": pending_apps,
        "accepted_apps": accepted_apps,
        "completed_apps": completed_apps,
        "rejected_apps": rejected_apps,
        "pending_reports_count": pending_reports_count,
        "total_reports_count": total_reports_count,
        "recent_verifications": recent_verifications,
        "recent_jobs": recent_jobs,
        "recent_applications": recent_applications,
        "recent_reports": recent_reports,
        # Backwards compatibility context variables
        "students": pending_verifications_qs,
        "rejected_students": students_qs.filter(is_rejected=True),
    }

    return render(request, "accounts/admin/dashboard.html", context)


# =========================================================
# STUDENT VERIFICATION MANAGEMENT
# =========================================================

@login_required
@user_passes_test(is_admin_user)
def admin_verifications(request):
    """Manage student ID verification queue, approve, reject, review IDs."""
    status_filter = request.GET.get('status', 'pending').strip().lower()
    search_q = request.GET.get('q', '').strip()

    students_qs = Student.objects.select_related('user', 'place').all().order_by('-id')

    if search_q:
        students_qs = students_qs.filter(
            Q(full_name__icontains=search_q) |
            Q(user__username__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(college__icontains=search_q) |
            Q(course__icontains=search_q) |
            Q(mobile__icontains=search_q)
        )

    # Status filter logic
    if status_filter == 'pending':
        filtered_students = students_qs.filter(is_verified=False, is_rejected=False).exclude(college_id__in=['', None])
    elif status_filter == 'verified':
        filtered_students = students_qs.filter(is_verified=True)
    elif status_filter == 'rejected':
        filtered_students = students_qs.filter(is_rejected=True)
    elif status_filter == 'missing':
        filtered_students = students_qs.filter(Q(college_id__in=['', None]) | Q(college_id=''), is_verified=False)
    else:
        status_filter = 'all'
        filtered_students = students_qs

    # Tab counts
    all_students_base = Student.objects.all()
    pending_count = all_students_base.filter(is_verified=False, is_rejected=False).exclude(college_id__in=['', None]).count()
    verified_count = all_students_base.filter(is_verified=True).count()
    rejected_count = all_students_base.filter(is_rejected=True).count()
    missing_count = all_students_base.filter(Q(college_id__in=['', None]) | Q(college_id=''), is_verified=False).count()
    all_count = all_students_base.count()

    context = {
        'students': filtered_students,
        'status_filter': status_filter,
        'search_q': search_q,
        'pending_count': pending_count,
        'verified_count': verified_count,
        'rejected_count': rejected_count,
        'missing_count': missing_count,
        'all_count': all_count,
    }
    return render(request, 'accounts/admin/verifications.html', context)


@login_required
@user_passes_test(is_admin_user)
def approve_student(request, student_id):
    """Approve a student's verification documents and notify them."""
    student = get_object_or_404(Student, id=student_id)
    student.is_verified = True
    student.is_rejected = False
    student.save()

    Notification.objects.create(
        student=student,
        message="Congratulations! Your college ID verification has been approved by admin. You can now explore and apply for jobs."
    )

    messages.success(request, f"Student '{student.full_name or student.user.username}' has been approved and verified.")
    
    redirect_url = request.META.get('HTTP_REFERER')
    if redirect_url and 'login' not in redirect_url:
        return redirect(redirect_url)
    return redirect('admin_verifications')


@login_required
@user_passes_test(is_admin_user)
def reject_student(request, student_id):
    """Reject a student's verification with an optional custom reason."""
    student = get_object_or_404(Student, id=student_id)
    
    reason = request.POST.get('reason', '').strip() or request.GET.get('reason', '').strip()
    if not reason:
        reason = "College ID document is unclear or invalid. Please re-upload a clear college ID."

    student.is_verified = False
    student.is_rejected = True
    student.save()

    Notification.objects.create(
        student=student,
        message=f"Verification Update: Your college ID verification was rejected. Reason: {reason}. Please re-upload your valid college ID."
    )

    messages.warning(request, f"Student '{student.full_name or student.user.username}' verification has been rejected.")
    
    redirect_url = request.META.get('HTTP_REFERER')
    if redirect_url and 'login' not in redirect_url:
        return redirect(redirect_url)
    return redirect('admin_verifications')


# =========================================================
# USER MANAGEMENT (STUDENTS, CUSTOMERS, ADMINS)
# =========================================================

@login_required
@user_passes_test(is_admin_user)
def admin_users(request):
    """List, search, filter, and manage all platform users."""
    role_filter = request.GET.get('role', 'all').strip().lower()
    status_filter = request.GET.get('status', 'all').strip().lower()
    search_q = request.GET.get('q', '').strip()

    users_qs = CustomUser.objects.prefetch_related('student_profile', 'customer_profile').all().order_by('-date_joined')

    # Role filter
    if role_filter == 'student':
        users_qs = users_qs.filter(user_type='student')
    elif role_filter == 'customer':
        users_qs = users_qs.filter(user_type='customer')
    elif role_filter == 'admin':
        users_qs = users_qs.filter(Q(user_type='admin') | Q(is_staff=True) | Q(is_superuser=True))

    # Status filter
    if status_filter == 'active':
        users_qs = users_qs.filter(is_active=True)
    elif status_filter == 'inactive':
        users_qs = users_qs.filter(is_active=False)
    elif status_filter == 'verified':
        users_qs = users_qs.filter(student_profile__is_verified=True)
    elif status_filter == 'unverified':
        users_qs = users_qs.filter(user_type='student', student_profile__is_verified=False)

    # Search filter
    if search_q:
        users_qs = users_qs.filter(
            Q(username__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(student_profile__full_name__icontains=search_q) |
            Q(customer_profile__full_name__icontains=search_q) |
            Q(student_profile__mobile__icontains=search_q) |
            Q(student_profile__college__icontains=search_q)
        ).distinct()

    # User counts
    all_users_base = CustomUser.objects.all()
    total_users_count = all_users_base.count()
    student_count = all_users_base.filter(user_type='student').count()
    customer_count = all_users_base.filter(user_type='customer').count()
    admin_count = all_users_base.filter(Q(user_type='admin') | Q(is_staff=True) | Q(is_superuser=True)).distinct().count()
    inactive_count = all_users_base.filter(is_active=False).count()

    create_form = AdminUserCreationForm()

    context = {
        'users': users_qs,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_q': search_q,
        'total_users_count': total_users_count,
        'student_count': student_count,
        'customer_count': customer_count,
        'admin_count': admin_count,
        'inactive_count': inactive_count,
        'create_form': create_form,
        'kerala_districts': KERALA_DISTRICTS,
    }
    return render(request, 'accounts/admin/users.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_user_create(request):
    """Admin create user endpoint with full validation."""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            messages.success(request, f"User '{new_user.username}' ({new_user.get_user_type_display()}) created successfully.")
            return redirect('admin_users')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.capitalize()}: {err}")
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin_user)
def admin_user_edit(request, user_id):
    """Admin edit user profile, active status, role details."""
    target_user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        is_active = (request.POST.get('is_active') == 'on') or (request.POST.get('is_active') == 'true')
        
        # Email uniqueness check
        if email and CustomUser.objects.filter(email=email).exclude(id=target_user.id).exists():
            messages.error(request, f"Email '{email}' is already in use by another account.")
            return redirect('admin_users')

        target_user.email = email
        target_user.is_active = is_active
        target_user.save()

        # Update Student Profile if applicable
        if target_user.user_type == 'student':
            student_profile, _ = Student.objects.get_or_create(user=target_user)
            student_profile.full_name = full_name
            student_profile.mobile = mobile
            student_profile.college = request.POST.get('college', '').strip()
            student_profile.course = request.POST.get('course', '').strip()
            student_profile.semester = request.POST.get('semester', '').strip()
            student_profile.district = request.POST.get('district', '').strip()
            student_profile.address = request.POST.get('address', '').strip()

            place_name = request.POST.get('place', '').strip()
            if place_name and student_profile.district:
                place_obj, _ = Place.objects.get_or_create(name=place_name, district=student_profile.district)
                student_profile.place = place_obj

            student_profile.is_verified = (request.POST.get('is_verified') == 'on') or (request.POST.get('is_verified') == 'true')
            student_profile.is_rejected = (request.POST.get('is_rejected') == 'on') or (request.POST.get('is_rejected') == 'true')
            student_profile.save()

        # Update Customer Profile if applicable
        elif target_user.user_type == 'customer':
            customer_profile, _ = Customer.objects.get_or_create(user=target_user)
            customer_profile.full_name = full_name
            customer_profile.email = email
            customer_profile.mobile_number = mobile
            customer_profile.address = request.POST.get('address', '').strip()
            customer_profile.save()

        messages.success(request, f"User '{target_user.username}' updated successfully.")
    
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin_user)
def admin_user_toggle_status(request, user_id):
    """Activate or deactivate user account."""
    target_user = get_object_or_404(CustomUser, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('admin_users')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"Account '{target_user.username}' has been {status_str}.")
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin_user)
def admin_user_delete(request, user_id):
    """Safely delete a user account and associated data."""
    target_user = get_object_or_404(CustomUser, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot delete your own admin account.")
        return redirect('admin_users')

    username = target_user.username
    target_user.delete()
    messages.success(request, f"User '{username}' was deleted successfully.")
    return redirect('admin_users')


# =========================================================
# JOB MANAGEMENT
# =========================================================

@login_required
@user_passes_test(is_admin_user)
def admin_jobs(request):
    """List, search, filter, and manage all posted jobs."""
    search_q = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '').strip()
    duration_filter = request.GET.get('duration', '').strip()
    customer_id = request.GET.get('customer', '').strip()

    jobs_qs = Job.objects.select_related('customer').annotate(
        applicant_count=Count('applications')
    ).order_by('-created_at')

    if search_q:
        jobs_qs = jobs_qs.filter(
            Q(job_title__icontains=search_q) |
            Q(description__icontains=search_q) |
            Q(required_skills__icontains=search_q) |
            Q(location__icontains=search_q) |
            Q(customer__username__icontains=search_q) |
            Q(customer__email__icontains=search_q)
        )

    if location_filter and location_filter != 'all':
        jobs_qs = jobs_qs.filter(location__iexact=location_filter)

    if duration_filter and duration_filter != 'all':
        jobs_qs = jobs_qs.filter(work_duration__iexact=duration_filter)

    if customer_id and customer_id != 'all':
        jobs_qs = jobs_qs.filter(customer_id=customer_id)

    distinct_locations = sorted(list(set(filter(None, Job.objects.values_list('location', flat=True)))))
    distinct_durations = ['2 Hours', '4 Hours', 'Half Day', 'Full Day', '2 Days', '1 Week', 'Custom']
    all_customers = CustomUser.objects.filter(user_type='customer')

    context = {
        'jobs': jobs_qs,
        'search_q': search_q,
        'location_filter': location_filter,
        'duration_filter': duration_filter,
        'customer_id': customer_id,
        'distinct_locations': distinct_locations,
        'distinct_durations': distinct_durations,
        'all_customers': all_customers,
        'total_jobs_count': Job.objects.count(),
    }
    return render(request, 'accounts/admin/jobs.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_job_edit(request, job_id):
    """Admin edit job listing details."""
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        form = AdminJobEditForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job '{job.job_title}' updated successfully.")
        else:
            messages.error(request, "Please check the job edit form errors.")
    return redirect('admin_jobs')


@login_required
@user_passes_test(is_admin_user)
def admin_job_delete(request, job_id):
    """Admin delete job listing."""
    job = get_object_or_404(Job, id=job_id)
    title = job.job_title
    job.delete()
    messages.success(request, f"Job '{title}' deleted successfully.")
    return redirect('admin_jobs')


# =========================================================
# APPLICATION MANAGEMENT
# =========================================================

@login_required
@user_passes_test(is_admin_user)
def admin_applications(request):
    """List, search, filter, and audit all student job applications."""
    status_filter = request.GET.get('status', 'all').strip()
    search_q = request.GET.get('q', '').strip()
    job_id = request.GET.get('job', '').strip()

    apps_qs = JobApplication.objects.select_related(
        'student', 'student__student_profile', 'job', 'job__customer'
    ).order_by('-applied_at')

    if status_filter and status_filter != 'all':
        apps_qs = apps_qs.filter(status__iexact=status_filter)

    if job_id and job_id != 'all':
        apps_qs = apps_qs.filter(job_id=job_id)

    if search_q:
        apps_qs = apps_qs.filter(
            Q(student__username__icontains=search_q) |
            Q(student__email__icontains=search_q) |
            Q(student__student_profile__full_name__icontains=search_q) |
            Q(job__job_title__icontains=search_q) |
            Q(job__customer__username__icontains=search_q)
        )

    # Status counts for tab counters
    all_apps_base = JobApplication.objects.all()
    total_apps_count = all_apps_base.count()
    pending_count = all_apps_base.filter(status='Pending').count()
    shortlisted_count = all_apps_base.filter(status='Shortlisted').count()
    accepted_count = all_apps_base.filter(status='Accepted').count()
    completed_count = all_apps_base.filter(status='Completed').count()
    rejected_count = all_apps_base.filter(status='Rejected').count()

    all_jobs = Job.objects.all().order_by('-created_at')

    context = {
        'applications': apps_qs,
        'status_filter': status_filter,
        'search_q': search_q,
        'job_id': job_id,
        'all_jobs': all_jobs,
        'total_apps_count': total_apps_count,
        'pending_count': pending_count,
        'shortlisted_count': shortlisted_count,
        'accepted_count': accepted_count,
        'completed_count': completed_count,
        'rejected_count': rejected_count,
        'status_choices': [s[0] for s in JobApplication.STATUS],
    }
    return render(request, 'accounts/admin/applications.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_application_status(request, app_id):
    """Admin manually override application status and notify student."""
    app_obj = get_object_or_404(JobApplication, id=app_id)
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        valid_statuses = [s[0] for s in JobApplication.STATUS]
        if new_status in valid_statuses:
            app_obj.status = new_status
            app_obj.save()

            student_profile = getattr(app_obj.student, 'student_profile', None)
            if student_profile:
                Notification.objects.create(
                    student=student_profile,
                    message=f"Admin Status Update: Your application for '{app_obj.job.job_title}' is now '{new_status}'."
                )

            messages.success(request, f"Application status updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid status choice.")

    return redirect('admin_applications')


@login_required
@user_passes_test(is_admin_user)
def admin_application_delete(request, app_id):
    """Admin delete application."""
    app_obj = get_object_or_404(JobApplication, id=app_id)
    app_obj.delete()
    messages.success(request, "Application deleted successfully.")
    return redirect('admin_applications')


# =========================================================
# REPORT & MODERATION MANAGEMENT
# =========================================================

@login_required
@user_passes_test(is_admin_user)
def admin_reports(request):
    """Moderation queue for user complaints, disputes, and violations."""
    status_filter = request.GET.get('status', 'all').strip()
    type_filter = request.GET.get('type', 'all').strip()
    search_q = request.GET.get('q', '').strip()

    reports_qs = Report.objects.select_related(
        'reporter', 'reported_user', 'reported_job', 'reported_review', 'resolved_by'
    ).all().order_by('-created_at')

    if status_filter and status_filter != 'all':
        reports_qs = reports_qs.filter(status__iexact=status_filter)

    if type_filter and type_filter != 'all':
        reports_qs = reports_qs.filter(report_type__iexact=type_filter)

    if search_q:
        reports_qs = reports_qs.filter(
            Q(reason__icontains=search_q) |
            Q(description__icontains=search_q) |
            Q(reporter__username__icontains=search_q) |
            Q(reported_user__username__icontains=search_q) |
            Q(reported_job__job_title__icontains=search_q)
        )

    all_reports_base = Report.objects.all()
    total_count = all_reports_base.count()
    pending_count = all_reports_base.filter(status='Pending').count()
    investigating_count = all_reports_base.filter(status='Investigating').count()
    resolved_count = all_reports_base.filter(status='Resolved').count()
    dismissed_count = all_reports_base.filter(status='Dismissed').count()

    context = {
        'reports': reports_qs,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search_q': search_q,
        'total_count': total_count,
        'pending_count': pending_count,
        'investigating_count': investigating_count,
        'resolved_count': resolved_count,
        'dismissed_count': dismissed_count,
        'report_types': Report.REPORT_TYPES,
        'status_choices': Report.STATUS_CHOICES,
        'action_choices': Report.ACTION_CHOICES,
    }
    return render(request, 'accounts/admin/reports.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_resolve_report(request, report_id):
    """Resolve, investigate, or dismiss a moderation report with actions."""
    report = get_object_or_404(Report, id=report_id)

    if request.method == 'POST':
        new_status = request.POST.get('status', 'Resolved').strip()
        action_taken = request.POST.get('action_taken', 'None').strip()
        admin_notes = request.POST.get('admin_notes', '').strip()

        report.status = new_status
        report.action_taken = action_taken
        report.admin_notes = admin_notes
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()

        # Automated moderation action triggers
        if action_taken == 'User Deactivated' and report.reported_user:
            report.reported_user.is_active = False
            report.reported_user.save()
            messages.warning(request, f"Reported user '{report.reported_user.username}' was deactivated.")

        elif action_taken == 'Job Removed' and report.reported_job:
            job_title = report.reported_job.job_title
            report.reported_job.delete()
            messages.warning(request, f"Reported job listing '{job_title}' was deleted.")

        elif action_taken == 'Review Removed' and report.reported_review:
            report.reported_review.delete()
            messages.warning(request, "Reported review was deleted.")

        elif action_taken == 'Warning Sent' and report.reported_user:
            student_prof = getattr(report.reported_user, 'student_profile', None)
            if student_prof:
                Notification.objects.create(
                    student=student_prof,
                    message=f"Official Notice from WorkBridge Admin: {admin_notes or 'Please ensure all activity complies with community rules.'}"
                )
            messages.info(request, f"Warning notification sent to '{report.reported_user.username}'.")

        messages.success(request, f"Report #{report.id} marked as '{new_status}'.")

    return redirect('admin_reports')


@login_required
def create_report(request):
    """Public/Authenticated endpoint to submit a report."""
    if request.method == 'POST':
        form = ReportCreationForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            messages.success(request, "Your report has been submitted to the administration team for investigation.")
        else:
            messages.error(request, "Unable to submit report. Please fill all required fields.")
    
    redirect_url = request.META.get('HTTP_REFERER') or reverse('home')
    return redirect(redirect_url)


# =========================================================
# CUSTOM HTTP ERROR HANDLERS
# =========================================================

def custom_page_not_found_view(request, exception=None):
    """Custom 404 Page Not Found error handler."""
    return render(request, '404.html', status=404)


def custom_permission_denied_view(request, exception=None):
    """Custom 403 Access Forbidden error handler."""
    return render(request, '403.html', status=403)


def custom_server_error_view(request):
    """Custom 500 Internal Server Error handler."""
    return render(request, '500.html', status=500)