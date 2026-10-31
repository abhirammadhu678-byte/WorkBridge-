from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import CustomUser, Portfolio, Place
from students.models import Student


class AdminLoginTests(TestCase):
    def test_admin_login_redirects_to_admin_dashboard(self):
        user = CustomUser.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='strongpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True,
        )

        response = self.client.post(
            reverse('login'),
            {'username': user.username, 'password': 'strongpass123'},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_dashboard'))


class AdminVerificationTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='strongpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True,
        )
        self.student = CustomUser.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='studentpass123',
            user_type='student'
        )
        self.student_profile = Student.objects.create(
            user=self.student,
            full_name='Test Student',
            college='Test College',
            is_verified=False
        )

    def test_admin_can_approve_student(self):
        self.client.login(username='adminuser', password='strongpass123')
        response = self.client.get(reverse('approve_student', args=[self.student_profile.id]))
        self.assertEqual(response.status_code, 302)
        self.student_profile.refresh_from_db()
        self.assertTrue(self.student_profile.is_verified)

    def test_admin_can_reject_student(self):
        self.client.login(username='adminuser', password='strongpass123')
        self.student_profile.college_id = SimpleUploadedFile("id.pdf", b"file_content", content_type="application/pdf")
        self.student_profile.save()

        response = self.client.get(reverse('reject_student', args=[self.student_profile.id]))
        self.assertEqual(response.status_code, 302)
        self.student_profile.refresh_from_db()
        self.assertFalse(self.student_profile.is_verified)
        self.assertTrue(self.student_profile.is_rejected)
        self.assertTrue(bool(self.student_profile.college_id))

    def test_non_admin_cannot_approve_student(self):
        self.client.login(username='studentuser', password='studentpass123')
        response = self.client.get(reverse('approve_student', args=[self.student_profile.id]))
        self.assertEqual(response.status_code, 302)
        self.student_profile.refresh_from_db()
        self.assertFalse(self.student_profile.is_verified)

    def test_unverified_student_cannot_login_if_pending(self):
        self.student_profile.college_id = SimpleUploadedFile("id.pdf", b"file_content", content_type="application/pdf")
        self.student_profile.save()

        response = self.client.post(
            reverse('login'),
            {'username': self.student.username, 'password': 'studentpass123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your registration request is pending admin approval")


class AccountsWorkflowTests(TestCase):
    def test_home_page_loads(self):
        res = self.client.get(reverse('home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'WorkBridge')

    def test_student_registration_workflow(self):
        res = self.client.get(reverse('student_register'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('student_register'), {
            'fullname': 'New Student',
            'email': 'newstudent@example.com',
            'mobile': '9876543210',
            'college': 'Model Engineering College',
            'course': 'Computer Science',
            'semester': 'S6',
            'address': 'Kochi',
            'district': 'Ernakulam',
            'place': 'Thrikkakara',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(email='newstudent@example.com').exists())
        self.assertTrue(Student.objects.filter(user__email='newstudent@example.com').exists())

    def test_student_profile_and_portfolio_views(self):
        user = CustomUser.objects.create_user(
            username='studprofile@example.com',
            email='studprofile@example.com',
            password='password123',
            user_type='student'
        )
        Student.objects.create(
            user=user,
            full_name='Profile Tester',
            is_verified=True
        )
        self.client.login(username='studprofile@example.com', password='password123')

        # Student Dashboard
        res = self.client.get(reverse('student_dashboard'))
        self.assertEqual(res.status_code, 200)

        # Profile GET and POST
        res = self.client.get(reverse('student_profile'))
        self.assertEqual(res.status_code, 200)

        # Post comprehensive profile update
        res = self.client.post(reverse('student_profile'), {
            'full_name': 'Profile Tester Updated',
            'mobile': '9876543210',
            'college': 'Government Engineering College Thrissur',
            'course': 'Computer Science & Engineering',
            'semester': 'Semester 6',
            'district': 'Thrissur',
            'place_name': 'Ramavarmapuram',
            'address': 'House No 42, Engineering Colony',
            'skills': 'Python, Django, React, PostgreSQL',
            'education': 'B.Tech in CSE with 8.5 CGPA',
            'experience': 'Freelance developer for 2 client websites',
            'about_me': 'Passionate about coding, AI, and scalable backend architecture.'
        })
        self.assertEqual(res.status_code, 302)

        # Verify all fields persisted in the database
        student_profile = Student.objects.get(user=user)
        self.assertEqual(student_profile.full_name, 'Profile Tester Updated')
        self.assertEqual(student_profile.mobile, '9876543210')
        self.assertEqual(student_profile.college, 'Government Engineering College Thrissur')
        self.assertEqual(student_profile.course, 'Computer Science & Engineering')
        self.assertEqual(student_profile.semester, 'Semester 6')
        self.assertEqual(student_profile.district, 'Thrissur')
        self.assertIsNotNone(student_profile.place)
        self.assertEqual(student_profile.place.name, 'Ramavarmapuram')
        self.assertEqual(student_profile.skills, 'Python, Django, React, PostgreSQL')
        self.assertEqual(student_profile.education, 'B.Tech in CSE with 8.5 CGPA')
        self.assertEqual(student_profile.experience, 'Freelance developer for 2 client websites')
        self.assertEqual(student_profile.about_me, 'Passionate about coding, AI, and scalable backend architecture.')

        # Verify profile GET displays updated data
        res_view = self.client.get(reverse('student_profile'))
        self.assertEqual(res_view.status_code, 200)
        self.assertContains(res_view, 'Profile Tester Updated')
        self.assertContains(res_view, 'Ramavarmapuram')
        self.assertContains(res_view, 'Python, Django, React, PostgreSQL')

        # Portfolio GET and POST
        res = self.client.get(reverse('portfolio'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('portfolio'), {
            'work_title': 'E-Commerce Project',
            'description': 'Full stack shop platform'
        })
        self.assertEqual(res.status_code, 302)
        portfolio_item = Portfolio.objects.filter(work_title='E-Commerce Project').first()
        self.assertIsNotNone(portfolio_item)

        # Delete Portfolio
        res = self.client.get(reverse('delete_portfolio', args=[portfolio_item.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Portfolio.objects.filter(id=portfolio_item.id).exists())

        # Logout
        res = self.client.get(reverse('logout'))
        self.assertEqual(res.status_code, 302)


# =========================================================
# COMPREHENSIVE ADMIN PORTAL TESTS
# =========================================================

from jobs.models import Job, JobApplication
from customers.models import Customer
from .models import Report
import datetime


class AdminPortalTestSuite(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin_boss',
            email='admin_boss@example.com',
            password='adminpassword123',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )

        self.student_user = CustomUser.objects.create_user(
            username='student_alice',
            email='alice@example.com',
            password='studentpass123',
            user_type='student'
        )
        self.student_profile = Student.objects.create(
            user=self.student_user,
            full_name='Alice Student',
            college='CET Trivandrum',
            course='B.Tech',
            semester='S5',
            is_verified=False
        )

        self.customer_user = CustomUser.objects.create_user(
            username='employer_bob',
            email='bob@example.com',
            password='customerpass123',
            user_type='customer'
        )
        self.customer_profile = Customer.objects.create(
            user=self.customer_user,
            full_name='Bob Employer',
            email='bob@example.com',
            mobile_number='9876543210'
        )

        self.job = Job.objects.create(
            customer=self.customer_user,
            job_title='Event Assistant',
            description='Help manage festival check-in counter.',
            location='Kochi',
            required_skills='Communication, Organization',
            work_date=datetime.date.today() + datetime.timedelta(days=3),
            work_duration='1 Day'
        )

        self.application = JobApplication.objects.create(
            student=self.student_user,
            job=self.job,
            cover_message='I have experience handling events.',
            availability='Full day available',
            status='Pending'
        )

    # -----------------------------------------------------
    # 1. Admin Dashboard Tests
    # -----------------------------------------------------
    def test_admin_dashboard_access_for_admin(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        res = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Executive Dashboard')
        self.assertContains(res, 'Event Assistant')
        self.assertEqual(res.context['total_users'], 3)
        self.assertEqual(res.context['total_jobs'], 1)

    def test_admin_dashboard_with_null_customer_job(self):
        # Create a job with customer=None
        Job.objects.create(
            customer=None,
            job_title='Community Volunteer',
            description='Volunteer for community drive.',
            location='Kozhikode',
            work_date=datetime.date.today(),
            work_duration='Half Day'
        )
        self.client.login(username='admin_boss', password='adminpassword123')
        res = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Community Volunteer')
        self.assertContains(res, 'System / Unassigned')

        # Test jobs page with null customer
        res_jobs = self.client.get(reverse('admin_jobs'))
        self.assertEqual(res_jobs.status_code, 200)
        self.assertContains(res_jobs, 'Unassigned / System')

    def test_admin_dashboard_denied_for_student(self):
        self.client.login(username='student_alice', password='studentpass123')

        res = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(res.status_code, 302)

    # -----------------------------------------------------
    # 2. Student Verification Tests
    # -----------------------------------------------------
    def test_admin_verifications_view_and_filters(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        
        # Upload ID
        self.student_profile.college_id = SimpleUploadedFile("id_card.png", b"file_bytes", content_type="image/png")
        self.student_profile.save()

        res = self.client.get(reverse('admin_verifications'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Alice Student')

        # Test Search
        res_search = self.client.get(reverse('admin_verifications') + '?q=Alice')
        self.assertEqual(len(res_search.context['students']), 1)

    def test_reject_student_with_custom_reason(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        self.student_profile.college_id = SimpleUploadedFile("id_card.png", b"file_bytes", content_type="image/png")
        self.student_profile.save()

        custom_reason = "ID card photo is blurry and college name not readable."
        res = self.client.post(
            reverse('reject_student_verification', args=[self.student_profile.id]),
            {'reason': custom_reason}
        )
        self.assertEqual(res.status_code, 302)
        
        self.student_profile.refresh_from_db()
        self.assertFalse(self.student_profile.is_verified)
        self.assertTrue(self.student_profile.is_rejected)

        # Check notification received with reason
        notif = self.student_profile.notifications.first()
        self.assertIsNotNone(notif)
        self.assertIn(custom_reason, notif.message)

    # -----------------------------------------------------
    # 3. User Management Tests
    # -----------------------------------------------------
    def test_admin_users_view_and_create(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        res = self.client.get(reverse('admin_users'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'student_alice')
        self.assertContains(res, 'employer_bob')

        # Create new student user via admin
        res_create = self.client.post(reverse('admin_user_create'), {
            'user_type': 'student',
            'username': 'new_candidate',
            'email': 'newcand@example.com',
            'full_name': 'New Candidate',
            'password': 'password123',
            'confirm_password': 'password123',
            'mobile': '9988776655',
            'college': 'GEC Thrissur',
            'course': 'MCA',
            'semester': 'S2',
            'district': 'Thrissur',
            'place': 'Thrissur Town',
            'is_active': 'on',
            'is_verified': 'on'
        })
        self.assertEqual(res_create.status_code, 302)
        created_user = CustomUser.objects.filter(username='new_candidate').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.user_type, 'student')
        self.assertTrue(created_user.student_profile.is_verified)

    def test_admin_user_edit_and_toggle_status(self):
        self.client.login(username='admin_boss', password='adminpassword123')

        # Toggle status to deactive
        res_toggle = self.client.get(reverse('admin_user_toggle_status', args=[self.student_user.id]))
        self.assertEqual(res_toggle.status_code, 302)
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.is_active)

        # Edit user
        res_edit = self.client.post(reverse('admin_user_edit', args=[self.student_user.id]), {
            'full_name': 'Alice Updated',
            'email': 'alice_updated@example.com',
            'mobile': '1122334455',
            'college': 'CET Updated',
            'course': 'M.Tech',
            'semester': 'S1',
            'is_active': 'on',
            'is_verified': 'on'
        })
        self.assertEqual(res_edit.status_code, 302)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.email, 'alice_updated@example.com')
        self.assertTrue(self.student_user.is_active)
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.full_name, 'Alice Updated')

    def test_admin_user_delete(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        user_to_delete = CustomUser.objects.create_user(
            username='temp_user',
            email='temp@example.com',
            password='password123'
        )
        res = self.client.post(reverse('admin_user_delete', args=[user_to_delete.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(CustomUser.objects.filter(id=user_to_delete.id).exists())

    # -----------------------------------------------------
    # 4. Job Management Tests
    # -----------------------------------------------------
    def test_admin_jobs_view_edit_delete(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        res = self.client.get(reverse('admin_jobs'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Event Assistant')

        # Edit Job
        res_edit = self.client.post(reverse('admin_job_edit', args=[self.job.id]), {
            'job_title': 'Lead Event Assistant',
            'customer': self.customer_user.id,
            'location': 'Ernakulam',
            'work_duration': '2 Days',
            'work_date': '2026-10-15',
            'required_skills': 'Leadership, Coordination',
            'description': 'Updated job description.'
        })
        self.assertEqual(res_edit.status_code, 302)
        self.job.refresh_from_db()
        self.assertEqual(self.job.job_title, 'Lead Event Assistant')

        # Delete Job
        res_delete = self.client.post(reverse('admin_job_delete', args=[self.job.id]))
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    # -----------------------------------------------------
    # 5. Application Management Tests
    # -----------------------------------------------------
    def test_admin_applications_status_change(self):
        self.client.login(username='admin_boss', password='adminpassword123')
        res = self.client.get(reverse('admin_applications'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Event Assistant')
        self.assertContains(res, 'Alice Student')

        # Change status
        res_status = self.client.post(
            reverse('admin_application_status', args=[self.application.id]),
            {'status': 'Shortlisted'}
        )
        self.assertEqual(res_status.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Shortlisted')

    # -----------------------------------------------------
    # 6. Report & Moderation Tests
    # -----------------------------------------------------
    def test_create_and_resolve_report(self):
        self.client.login(username='student_alice', password='studentpass123')
        
        # Student submits a report
        res_submit = self.client.post(reverse('create_report'), {
            'report_type': 'job',
            'reported_job': self.job.id,
            'reason': 'spam',
            'description': 'This job posting seems like spam promotional content.'
        })
        self.assertEqual(res_submit.status_code, 302)
        report = Report.objects.filter(reported_job=self.job).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.status, 'Pending')

        # Admin inspects and resolves report
        self.client.login(username='admin_boss', password='adminpassword123')
        res_reports_view = self.client.get(reverse('admin_reports'))
        self.assertEqual(res_reports_view.status_code, 200)
        self.assertContains(res_reports_view, report.description)

        # Resolve report with action
        res_resolve = self.client.post(reverse('admin_resolve_report', args=[report.id]), {
            'status': 'Resolved',
            'action_taken': 'Warning Sent',
            'admin_notes': 'Reviewed and confirmed. Warning issued to poster.'
        })
        self.assertEqual(res_resolve.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, 'Resolved')
        self.assertEqual(report.action_taken, 'Warning Sent')
        self.assertEqual(report.resolved_by, self.admin)


# =========================================================
# SECURITY & QUALITY ASSURANCE TEST SUITE
# =========================================================

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from accounts.validators import (
    validate_image_file,
    validate_document_file,
    validate_verification_doc,
    validate_portfolio_image,
    validate_video_file,
    validate_mobile_number,
)
from accounts.views import (
    custom_page_not_found_view,
    custom_permission_denied_view,
    custom_server_error_view,
)
from accounts.forms import StudentRegistrationForm


class SecurityAndQualityTestSuite(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Active Student
        self.student_user = CustomUser.objects.create_user(
            username='active_student',
            email='student_active@example.com',
            password='password123',
            user_type='student'
        )
        self.student_profile = Student.objects.create(
            user=self.student_user,
            full_name='Active Student',
            is_verified=True
        )

        # Active Customer
        self.customer_user = CustomUser.objects.create_user(
            username='active_customer',
            email='customer_active@example.com',
            password='password123',
            user_type='customer'
        )
        self.customer_profile = Customer.objects.create(
            user=self.customer_user,
            full_name='Active Customer',
            email='customer_active@example.com',
            mobile_number='9876543210'
        )

        # Deactivated User
        self.deactivated_user = CustomUser.objects.create_user(
            username='deactivated_user',
            email='deactivated@example.com',
            password='password123',
            user_type='student',
            is_active=False
        )

    # -----------------------------------------------------
    # 1. Authentication & Deactivation Security
    # -----------------------------------------------------
    def test_deactivated_user_cannot_authenticate_or_login(self):
        # authenticate() directly
        auth_result = authenticate(username='deactivated_user', password='password123')
        self.assertIsNone(auth_result)

        # Attempt login via POST view
        res = self.client.post(
            reverse('login'),
            {'username': 'deactivated_user', 'password': 'password123'}
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Login failed')

        # Check session is not authenticated
        self.assertNotIn('_auth_user_id', self.client.session)

    # -----------------------------------------------------
    # 2. File & Media Upload Validators
    # -----------------------------------------------------
    def test_image_validator_accepted_and_rejected(self):
        # Valid PNG
        valid_img = SimpleUploadedFile("avatar.png", b"imagebytes", content_type="image/png")
        self.assertIsNone(validate_image_file(valid_img))

        # Valid JPG
        valid_jpg = SimpleUploadedFile("avatar.jpg", b"imagebytes", content_type="image/jpeg")
        self.assertIsNone(validate_image_file(valid_jpg))

        # Invalid format: executable
        bad_ext = SimpleUploadedFile("danger.exe", b"bytes", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_image_file(bad_ext)

        # Invalid size: > 5MB
        big_img = SimpleUploadedFile("huge.png", b"0" * (6 * 1024 * 1024), content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_image_file(big_img)

    def test_document_validator_accepted_and_rejected(self):
        # Valid PDF
        valid_pdf = SimpleUploadedFile("resume.pdf", b"pdfbytes", content_type="application/pdf")
        self.assertIsNone(validate_document_file(valid_pdf))

        # Valid DOCX
        valid_docx = SimpleUploadedFile("resume.docx", b"docxbytes", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIsNone(validate_document_file(valid_docx))

        # Invalid format: script
        bad_doc = SimpleUploadedFile("hack.sh", b"echo pwned", content_type="text/plain")
        with self.assertRaises(ValidationError):
            validate_document_file(bad_doc)

        # Invalid size: > 10MB
        big_doc = SimpleUploadedFile("large_doc.pdf", b"0" * (11 * 1024 * 1024), content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_document_file(big_doc)

    def test_video_validator_accepted_and_rejected(self):
        # Valid MP4
        valid_vid = SimpleUploadedFile("reel.mp4", b"videobytes", content_type="video/mp4")
        self.assertIsNone(validate_video_file(valid_vid))

        # Invalid format: ZIP archive
        bad_vid = SimpleUploadedFile("bundle.zip", b"zipdata", content_type="application/zip")
        with self.assertRaises(ValidationError):
            validate_video_file(bad_vid)

        # Invalid size: > 25MB
        big_vid = SimpleUploadedFile("huge_reel.mp4", b"0" * (26 * 1024 * 1024), content_type="video/mp4")
        with self.assertRaises(ValidationError):
            validate_video_file(big_vid)

    def test_mobile_number_validator(self):
        # Valid 10-digit formats
        self.assertEqual(validate_mobile_number("9876543210"), "9876543210")
        self.assertEqual(validate_mobile_number("+91 9876543210"), "9876543210")
        self.assertEqual(validate_mobile_number("91-8887776665"), "8887776665")
        self.assertEqual(validate_mobile_number("7012345678"), "7012345678")
        self.assertEqual(validate_mobile_number("6234567890"), "6234567890")

        # Invalid formats
        with self.assertRaises(ValidationError):
            validate_mobile_number("12345")
        with self.assertRaises(ValidationError):
            validate_mobile_number("abcdefghij")
        with self.assertRaises(ValidationError):
            validate_mobile_number("5987654321")  # Doesn't start with 6-9
        with self.assertRaises(ValidationError):
            validate_mobile_number("987654321000")  # Too long

    # -----------------------------------------------------
    # 3. Custom Error Handlers & Pages
    # -----------------------------------------------------
    def test_custom_404_page(self):
        res = self.client.get('/definitely-non-existent-route-xyz-404/')
        self.assertEqual(res.status_code, 404)
        self.assertContains(res, 'Page Not Found', status_code=404)
        self.assertContains(res, 'WorkBridge', status_code=404)

    def test_custom_403_view(self):
        req = self.factory.get('/forbidden/')
        res = custom_permission_denied_view(req)
        self.assertEqual(res.status_code, 403)
        self.assertIn(b'Access Denied', res.content)

    def test_custom_500_view(self):
        req = self.factory.get('/server-error/')
        res = custom_server_error_view(req)
        self.assertEqual(res.status_code, 500)
        self.assertIn(b'Server Error', res.content)

    # -----------------------------------------------------
    # 4. Cross-Role Authorization Guards
    # -----------------------------------------------------
    def test_student_cannot_access_customer_portal(self):
        self.client.login(username='active_student', password='password123')

        # Customer Dashboard
        res = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(res.status_code, 302)

        # Job Post
        res = self.client.get(reverse('job_post'))
        self.assertEqual(res.status_code, 302)

        # My Jobs
        res = self.client.get(reverse('my_jobs'))
        self.assertEqual(res.status_code, 302)

        # Applicant Selection
        res = self.client.get(reverse('applicant_selection'))
        self.assertEqual(res.status_code, 302)

    def test_customer_cannot_access_student_portal_or_apply(self):
        self.client.login(username='active_customer', password='password123')

        # Student Dashboard
        res = self.client.get(reverse('student_dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('customer_dashboard'))

        # Applied Jobs
        res = self.client.get(reverse('applied_jobs'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('customer_dashboard'))

        # Student Profile
        res = self.client.get(reverse('student_profile'))
        self.assertEqual(res.status_code, 302)

        # Portfolio Upload
        res = self.client.get(reverse('portfolio'))
        self.assertEqual(res.status_code, 302)

    # -----------------------------------------------------
    # 5. Form & Media Validation Edge Cases
    # -----------------------------------------------------
    def test_student_registration_form_mismatched_passwords(self):
        form = StudentRegistrationForm(data={
            'fullname': 'Mismatch User',
            'email': 'mismatch@example.com',
            'mobile': '9876543210',
            'place': 'Kochi',
            'district': 'Ernakulam',
            'college': 'MEC',
            'course': 'CSE',
            'semester': 'S4',
            'address': 'Kochi',
            'password': 'password123',
            'confirm_password': 'password456'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('Passwords do not match.', form.non_field_errors())

    def test_student_registration_form_invalid_phone(self):
        form = StudentRegistrationForm(data={
            'fullname': 'Bad Phone User',
            'email': 'badphone@example.com',
            'mobile': '12345',
            'place': 'Kochi',
            'district': 'Ernakulam',
            'college': 'MEC',
            'course': 'CSE',
            'semester': 'S4',
            'address': 'Kochi',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('mobile', form.errors)

    def test_customer_registration_duplicate_email(self):
        # active_customer already has email customer_active@example.com
        res = self.client.post(reverse('customer_register'), {
            'name': 'Duplicate Bob',
            'email': 'customer_active@example.com',
            'mobile': '9876543210',
            'address': 'Kochi',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'A user with this email already exists')


