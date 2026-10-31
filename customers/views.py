from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Avg, Count, Q

from .models import Customer, WorkCompletion, Review
from accounts.models import CustomUser, Portfolio
from jobs.models import Job, JobApplication
from jobs.forms import JobPostForm
from students.models import Notification, Student


def send_student_notification(student_user, message):
    """Helper to send a notification to a student's profile if it exists."""
    student_profile = getattr(student_user, 'student_profile', None)
    if not student_profile and isinstance(student_user, CustomUser):
        student_profile = Student.objects.filter(user=student_user).first()
    if student_profile:
        Notification.objects.create(student=student_profile, message=message)


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

@login_required
def customer_dashboard(request):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        return redirect('home')

    # All jobs posted by this customer
    jobs_qs = Job.objects.filter(customer=request.user).order_by('-created_at')
    total_jobs = jobs_qs.count()

    # All applications for this customer's jobs
    applications_qs = JobApplication.objects.filter(
        job__customer=request.user
    ).select_related('student', 'job')

    total_applications = applications_qs.count()
    pending_applications = applications_qs.filter(status='Pending').count()
    shortlisted_applications = applications_qs.filter(status='Shortlisted').count()
    accepted_jobs = applications_qs.filter(status='Accepted').count()
    completed_jobs = applications_qs.filter(status='Completed').count()

    # Recent jobs with applicant count annotations
    recent_jobs = jobs_qs.annotate(
        applicant_count=Count('applications')
    )[:5]

    # Recent applications across customer jobs
    recent_applications = applications_qs.order_by('-applied_at')[:6]

    # Build enriched student data for recent applications
    recent_apps_data = []
    for app in recent_applications:
        student_profile = getattr(app.student, 'student_profile', None) or Student.objects.filter(user=app.student).first()
        recent_apps_data.append({
            'application': app,
            'student_name': (student_profile.full_name if student_profile and student_profile.full_name else app.student.username),
            'student_skills': student_profile.skills if student_profile else '',
            'student_photo': student_profile.profile_photo if student_profile else None,
            'is_verified': student_profile.is_verified if student_profile else False,
            'status': app.status,
            'applied_at': app.applied_at,
        })

    # Recent reviews given
    recent_reviews = Review.objects.filter(
        customer=request.user
    ).select_related('student', 'job').order_by('-created_at')[:5]

    customer_profile = getattr(request.user, 'customer_profile', None) or Customer.objects.filter(user=request.user).first()

    return render(
        request,
        'customers/customer_dashboard.html',
        {
            'customer_profile': customer_profile,
            'jobs': recent_jobs,
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'shortlisted_applications': shortlisted_applications,
            'accepted_jobs': accepted_jobs,
            'completed_jobs': completed_jobs,
            'recent_applications': recent_apps_data,
            'recent_reviews': recent_reviews,
        }
    )


# =========================================================
# CUSTOMER REGISTRATION
# =========================================================

def customer_register(request):
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        address = request.POST.get('address', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Password check
        if password != confirm_password:
            return render(
                request,
                'customers/customer_register.html',
                {
                    'error': 'Passwords do not match.'
                }
            )

        # Check existing email
        if CustomUser.objects.filter(email=email).exists() or CustomUser.objects.filter(username=email).exists():
            return render(
                request,
                'customers/customer_register.html',
                {
                    'error': 'A user with this email already exists.'
                }
            )

        # Create CustomUser
        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password,
            user_type='customer'
        )

        # Create Customer profile
        Customer.objects.create(
            user=user,
            full_name=name,
            email=email,
            mobile_number=mobile,
            address=address,
            password=make_password(password)
        )

        return render(
            request,
            'customers/customer_register.html',
            {
                'success': True
            }
        )

    return render(
        request,
        'customers/customer_register.html'
    )


# =========================================================
# JOB POSTING & EDITING
# =========================================================

@login_required
def job_post(request):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    if request.method == "POST":
        form = JobPostForm(request.POST)
        if form.is_valid():
            work_date = form.cleaned_data.get('work_date')
            if work_date and work_date < date.today():
                form.add_error('work_date', 'Work date cannot be in the past.')
                return render(
                    request,
                    'customers/jobpost.html',
                    {
                        'form': form,
                        'is_edit': False
                    }
                )

            job = form.save(commit=False)
            job.customer = request.user
            job.save()
            messages.success(request, f"Job '{job.job_title}' posted successfully!")
            return redirect('my_jobs')
    else:
        form = JobPostForm()

    return render(
        request,
        'customers/jobpost.html',
        {
            'form': form,
            'is_edit': False
        }
    )


@login_required
def job_edit(request, job_id):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    job = get_object_or_404(Job, id=job_id, customer=request.user)
    if request.method == "POST":
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            work_date = form.cleaned_data.get('work_date')
            if work_date and work_date < date.today():
                form.add_error('work_date', 'Work date cannot be in the past.')
                return render(
                    request,
                    'customers/jobpost.html',
                    {
                        'form': form,
                        'is_edit': True,
                        'job': job
                    }
                )

            form.save()
            messages.success(request, f"Job '{job.job_title}' updated successfully!")
            return redirect('my_jobs')
    else:
        form = JobPostForm(instance=job)

    return render(
        request,
        'customers/jobpost.html',
        {
            'form': form,
            'is_edit': True,
            'job': job
        }
    )


@login_required
def job_delete(request, job_id):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    job = get_object_or_404(Job, id=job_id, customer=request.user)
    job_title = job.job_title
    job.delete()
    messages.success(request, f"Job '{job_title}' deleted successfully.")
    return redirect('my_jobs')


# =========================================================
# MY JOBS
# =========================================================

@login_required
def my_jobs(request):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    jobs = Job.objects.filter(
        customer=request.user
    ).annotate(
        total_applicants=Count('applications'),
        pending_count=Count('applications', filter=Q(applications__status='Pending')),
        shortlisted_count=Count('applications', filter=Q(applications__status='Shortlisted')),
        accepted_count=Count('applications', filter=Q(applications__status='Accepted')),
        completed_count=Count('applications', filter=Q(applications__status='Completed'))
    ).order_by('-created_at')

    return render(
        request,
        'customers/my_jobs.html',
        {
            'jobs': jobs,
            'total_jobs_count': jobs.count()
        }
    )


# =========================================================
# APPLICANTS FOR A SPECIFIC JOB
# =========================================================

@login_required
def applicants_for_job(request, job_id):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    job = get_object_or_404(Job, id=job_id, customer=request.user)
    first_app = JobApplication.objects.filter(job=job).order_by('-applied_at').first()

    if first_app:
        return redirect(f"/customers/applicant-selection/{first_app.id}/?job_id={job.id}")

    return render(
        request,
        'customers/applicant_selection.html',
        {
            'application': None,
            'job': job,
            'job_id': job.id,
            'student': None,
            'applicant': None,
            'portfolios': [],
            'reviews': [],
            'all_applications': []
        }
    )


# =========================================================
# APPLICANT SELECTION & FULL PROFILE / PORTFOLIO VIEW
# =========================================================

@login_required
def applicant_selection(request, application_id=None):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    job_id_param = request.GET.get('job_id')
    
    # Base queryset for this customer's applications
    all_apps_qs = JobApplication.objects.select_related('student', 'job').filter(
        job__customer=request.user
    ).order_by('-applied_at')

    selected_job = None
    if job_id_param:
        try:
            job_id_int = int(job_id_param)
            selected_job = Job.objects.filter(id=job_id_int, customer=request.user).first()
            if selected_job:
                all_apps_qs = all_apps_qs.filter(job=selected_job)
        except (ValueError, TypeError):
            pass

    if application_id:
        application = get_object_or_404(
            JobApplication.objects.select_related('student', 'job'),
            id=application_id,
            job__customer=request.user
        )
    else:
        application = all_apps_qs.first()

    if not application:
        return render(
            request,
            'customers/applicant_selection.html',
            {
                'application': None,
                'job': selected_job,
                'job_id': selected_job.id if selected_job else None,
                'student': None,
                'applicant': None,
                'portfolios': [],
                'reviews': [],
                'all_applications': []
            }
        )

    # Handle POST action (shortlist, hire, accept, reject)
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'shortlist':
            application.status = 'Shortlisted'
            application.save()
            send_student_notification(
                application.student,
                f"You have been shortlisted for '{application.job.job_title}'."
            )
            messages.success(request, f"Applicant {application.student.username} shortlisted successfully.")
        elif action in ('hire', 'accept'):
            application.status = 'Accepted'
            application.save()
            send_student_notification(
                application.student,
                f"Congratulations! You were accepted for '{application.job.job_title}'."
            )
            messages.success(request, f"Applicant {application.student.username} accepted for this job!")
        elif action == 'reject':
            application.status = 'Rejected'
            application.save()
            send_student_notification(
                application.student,
                f"Your application for '{application.job.job_title}' was not selected."
            )
            messages.info(request, f"Application for {application.student.username} marked as rejected.")

        redirect_url = f"/customers/applicant-selection/{application.id}/"
        if selected_job:
            redirect_url += f"?job_id={selected_job.id}"
        return redirect(redirect_url)

    student_user = application.student
    student_profile = getattr(student_user, 'student_profile', None)
    if not student_profile:
        student_profile = Student.objects.filter(user=student_user).first()

    # Fetch all portfolio items for this student
    portfolios = []
    if student_profile:
        portfolios = Portfolio.objects.filter(student=student_profile).order_by('-uploaded_at')
    else:
        portfolios = Portfolio.objects.filter(student__user=student_user).order_by('-uploaded_at')

    # Fetch student's past reviews and rating average
    student_reviews = Review.objects.filter(student=student_user).select_related('customer', 'job').order_by('-created_at')
    avg_rating_val = student_reviews.aggregate(Avg('rating'))['rating__avg']
    rating_display = f"{round(avg_rating_val, 1)} / 5" if avg_rating_val else "No rating yet"
    avg_stars_num = round(avg_rating_val) if avg_rating_val else 0

    applicant_data = {
        'id': application.id,
        'full_name': (student_profile.full_name if student_profile and student_profile.full_name else student_user.username),
        'email': student_user.email,
        'mobile': student_profile.mobile if student_profile else '',
        'skills': student_profile.skills if student_profile else '',
        'skills_list': [s.strip() for s in student_profile.skills.split(',') if s.strip()] if student_profile and student_profile.skills else [],
        'rating': rating_display,
        'avg_stars': avg_stars_num,
        'reviews_count': student_reviews.count(),
        'college': student_profile.college if student_profile else '',
        'course': student_profile.course if student_profile else '',
        'semester': student_profile.semester if student_profile else '',
        'district': student_profile.district if student_profile else '',
        'place': student_profile.place.name if student_profile and student_profile.place else '',
        'education': student_profile.education if student_profile else '',
        'experience': student_profile.experience if student_profile else '',
        'about_me': student_profile.about_me if student_profile else '',
        'resume': student_profile.resume if student_profile else None,
        'profile_photo': student_profile.profile_photo if student_profile else None,
        'is_verified': student_profile.is_verified if student_profile else False,
    }

    # Prepare all applications for the left sidebar list
    sidebar_applications = []
    for app in all_apps_qs:
        st_prof = getattr(app.student, 'student_profile', None) or Student.objects.filter(user=app.student).first()
        sidebar_applications.append({
            'id': app.id,
            'student_name': st_prof.full_name if st_prof and st_prof.full_name else app.student.username,
            'job_title': app.job.job_title,
            'status': app.status,
            'applied_at': app.applied_at,
            'photo': st_prof.profile_photo if st_prof else None,
            'is_verified': st_prof.is_verified if st_prof else False,
            'skills': st_prof.skills if st_prof else '',
            'college': st_prof.college if st_prof else '',
            'is_current': app.id == application.id
        })

    return render(
        request,
        'customers/applicant_selection.html',
        {
            'application': application,
            'job': application.job,
            'job_id': selected_job.id if selected_job else application.job.id,
            'student': student_profile or student_user,
            'applicant': applicant_data,
            'portfolio': portfolios.first() if portfolios.exists() else None,
            'portfolios': portfolios,
            'reviews': student_reviews[:5],
            'all_applications': sidebar_applications,
            'all_jobs': Job.objects.filter(customer=request.user).order_by('-created_at')
        }
    )


# =========================================================
# SHORTLIST / ACCEPT / REJECT APPLICATION
# =========================================================

@login_required
def manage_application(request, application_id, action):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    application = get_object_or_404(
        JobApplication.objects.select_related('student', 'job'),
        id=application_id,
        job__customer=request.user
    )

    if request.method == "POST":
        if action == 'shortlist':
            application.status = 'Shortlisted'
            application.save()
            send_student_notification(
                application.student,
                f"You have been shortlisted for '{application.job.job_title}'."
            )
            messages.success(request, f"Applicant shortlisted for '{application.job.job_title}'.")
        elif action in ('accept', 'hire'):
            application.status = 'Accepted'
            application.save()
            send_student_notification(
                application.student,
                f"Congratulations! You have been accepted for '{application.job.job_title}'."
            )
            messages.success(request, f"Applicant accepted for '{application.job.job_title}'.")
        elif action == 'reject':
            application.status = 'Rejected'
            application.save()
            send_student_notification(
                application.student,
                f"Your application for '{application.job.job_title}' was rejected."
            )
            messages.info(request, f"Application rejected for '{application.job.job_title}'.")

    return redirect('applicant_selection', application_id=application.id)


# =========================================================
# WORK COMPLETION
# =========================================================

@login_required
def work_completion(request, application_id=None):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    if application_id:
        application = get_object_or_404(
            JobApplication.objects.select_related('student', 'job'),
            id=application_id,
            job__customer=request.user
        )
    else:
        # Fallback: look for accepted or in-progress application
        application = JobApplication.objects.select_related(
            'student',
            'job'
        ).filter(
            job__customer=request.user,
            status__in=['Accepted', 'Shortlisted', 'Completed']
        ).order_by('-applied_at').first()

    if not application:
        messages.warning(request, "No eligible active job applications found for work completion.")
        return redirect('customer_dashboard')

    student_profile = getattr(application.student, 'student_profile', None) or Student.objects.filter(user=application.student).first()

    if request.method == "POST":
        completion_date_str = request.POST.get('completion_date')
        work_status = request.POST.get('work_status', 'Completed')
        remarks = request.POST.get('remarks', '').strip()

        # Date validation
        try:
            c_date = date.fromisoformat(completion_date_str) if completion_date_str else date.today()
            if c_date > date.today():
                messages.error(request, "Completion date cannot be in the future.")
                return render(
                    request,
                    'customers/work_completion.html',
                    {
                        'application': application,
                        'job': application.job,
                        'student': student_profile or application.student,
                        'error': 'Completion date cannot be in the future.'
                    }
                )
        except ValueError:
            c_date = date.today()

        # Remarks validation for partial/incomplete
        if work_status != 'Completed' and not remarks:
            messages.error(request, "Remarks are required when work is not fully completed.")
            return render(
                request,
                'customers/work_completion.html',
                {
                    'application': application,
                    'job': application.job,
                    'student': student_profile or application.student,
                    'error': 'Remarks are required when work is not fully completed.'
                }
            )

        WorkCompletion.objects.create(
            application=application,
            job=application.job,
            completion_date=c_date,
            work_status=work_status,
            remarks=remarks,
            completed_by=request.user
        )

        application.status = 'Completed'
        application.save()

        send_student_notification(
            application.student,
            f"Work on '{application.job.job_title}' has been marked as '{work_status}'."
        )

        messages.success(request, f"Work marked as '{work_status}'! Please leave a review for the student.")
        return redirect('rating_review', application_id=application.id)

    # Active applications list for quick switching
    active_apps = JobApplication.objects.filter(
        job__customer=request.user,
        status__in=['Accepted', 'Completed']
    ).select_related('student', 'job')

    return render(
        request,
        'customers/work_completion.html',
        {
            'application': application,
            'job': application.job,
            'student': student_profile or application.student,
            'active_apps': active_apps,
            'today_date': date.today().isoformat()
        }
    )


# =========================================================
# RATING AND REVIEW
# =========================================================

@login_required
def rating_review(request, application_id=None):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to employer/customer accounts.")
        return redirect('student_dashboard' if request.user.user_type == 'student' else 'home')

    if application_id:
        application = get_object_or_404(
            JobApplication.objects.select_related('student', 'job'),
            id=application_id,
            job__customer=request.user
        )
    else:
        application = JobApplication.objects.select_related(
            'student',
            'job'
        ).filter(
            job__customer=request.user,
            status='Completed'
        ).order_by('-applied_at').first()

    if not application:
        messages.warning(request, "No completed job application found to review.")
        return redirect('customer_dashboard')

    student_user = application.student
    student_profile = getattr(student_user, 'student_profile', None) or Student.objects.filter(user=student_user).first()

    # Check for existing review
    existing_review = Review.objects.filter(
        application=application,
        customer=request.user
    ).first()

    if request.method == "POST":
        rating = request.POST.get('rating', '5')
        review_comment = request.POST.get('review_comment', '').strip()

        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                rating_val = 5
        except (ValueError, TypeError):
            rating_val = 5

        if existing_review:
            existing_review.rating = rating_val
            existing_review.review_comment = review_comment
            existing_review.save()
            messages.success(request, "Review updated successfully!")
        else:
            Review.objects.create(
                application=application,
                student=student_user,
                customer=request.user,
                job=application.job,
                rating=rating_val,
                review_comment=review_comment
            )
            messages.success(request, f"Review submitted successfully for {student_profile.full_name if student_profile else student_user.username}!")

        send_student_notification(
            student_user,
            f"You received a {rating_val}⭐ review for '{application.job.job_title}'!"
        )

        return redirect('customer_dashboard')

    # Completed jobs eligible for review
    completed_apps = JobApplication.objects.filter(
        job__customer=request.user,
        status='Completed'
    ).select_related('student', 'job')

    return render(
        request,
        'customers/rating_review.html',
        {
            'application': application,
            'job': application.job,
            'student': student_profile or student_user,
            'existing_review': existing_review,
            'completed_apps': completed_apps
        }
    )