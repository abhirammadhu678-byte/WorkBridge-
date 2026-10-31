from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, Portfolio
from students.models import Student, Notification
from jobs.models import Job, JobApplication
from customers.models import Customer, WorkCompletion, Review


class CustomerViewsAndModelTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Customer User
        self.customer_user = CustomUser.objects.create_user(
            username='cust@example.com',
            email='cust@example.com',
            password='password123',
            user_type='customer'
        )
        self.customer_profile = Customer.objects.create(
            user=self.customer_user,
            full_name='Customer Boss',
            email='cust@example.com',
            mobile_number='9876543210',
            address='Kochi, Kerala'
        )

        # Create Student User
        self.student_user = CustomUser.objects.create_user(
            username='stud@example.com',
            email='stud@example.com',
            password='password123',
            user_type='student'
        )
        self.student_profile = Student.objects.create(
            user=self.student_user,
            full_name='Student Worker',
            skills='Python, Django, Graphic Design',
            college='CUSAT',
            course='B.Tech Computer Science',
            semester='6',
            is_verified=True
        )

        # Create Student Portfolio
        self.portfolio = Portfolio.objects.create(
            student=self.student_profile,
            work_title='E-Commerce Prototype',
            description='Built a responsive e-commerce web application with Django and Stripe.'
        )

        # Create a Job
        future_date = (date.today() + timedelta(days=5)).isoformat()
        self.job = Job.objects.create(
            customer=self.customer_user,
            job_title='Web Designer Needed',
            description='Build a clean website layout',
            location='Ernakulam',
            required_skills='HTML, CSS, JS',
            work_date=future_date,
            work_duration='2 Days'
        )

        # Create a Job Application
        self.application = JobApplication.objects.create(
            student=self.student_user,
            job=self.job,
            cover_message='I have 3 years of web design experience and can complete this efficiently.',
            availability='Immediately',
            status='Pending'
        )

    def test_customer_register_get_and_post(self):
        # GET
        res = self.client.get(reverse('customer_register'))
        self.assertEqual(res.status_code, 200)

        # POST Password Mismatch
        res = self.client.post(reverse('customer_register'), {
            'name': 'New Employer',
            'email': 'newemp@example.com',
            'mobile': '9998887776',
            'address': 'Trivandrum',
            'password': 'pass1',
            'confirm_password': 'pass2'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Passwords do not match')

        # POST Successful Registration
        res = self.client.post(reverse('customer_register'), {
            'name': 'New Employer',
            'email': 'newemp@example.com',
            'mobile': '9998887776',
            'address': 'Trivandrum',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(email='newemp@example.com').exists())
        self.assertTrue(Customer.objects.filter(email='newemp@example.com').exists())

    def test_customer_dashboard_access(self):
        # Anonymous redirect
        res = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(res.status_code, 302)

        # Customer login
        self.client.login(username='cust@example.com', password='password123')
        res = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['total_jobs'], 1)
        self.assertEqual(res.context['total_applications'], 1)
        self.assertEqual(res.context['pending_applications'], 1)

    def test_job_post_validation_and_creation(self):
        self.client.login(username='cust@example.com', password='password123')

        # GET job post page
        res = self.client.get(reverse('job_post'))
        self.assertEqual(res.status_code, 200)

        # POST with past date
        past_date = (date.today() - timedelta(days=2)).isoformat()
        res = self.client.post(reverse('job_post'), {
            'job_title': 'Event Photographer',
            'description': 'Cover our college tech symposium',
            'location': 'Kochi',
            'required_skills': 'Photography, Lightroom',
            'work_date': past_date,
            'work_duration': 'Full Day'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Work date cannot be in the past')

        # POST valid job
        valid_date = (date.today() + timedelta(days=7)).isoformat()
        res = self.client.post(reverse('job_post'), {
            'job_title': 'Event Photographer',
            'description': 'Cover our college tech symposium',
            'location': 'Kochi',
            'required_skills': 'Photography, Lightroom',
            'work_date': valid_date,
            'work_duration': 'Full Day'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Job.objects.filter(job_title='Event Photographer').exists())

    def test_my_jobs_view(self):
        self.client.login(username='cust@example.com', password='password123')
        res = self.client.get(reverse('my_jobs'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Web Designer Needed')
        self.assertEqual(res.context['total_jobs_count'], 1)

    def test_job_edit_and_delete(self):
        self.client.login(username='cust@example.com', password='password123')
        
        # GET edit
        res = self.client.get(reverse('job_edit', args=[self.job.id]))
        self.assertEqual(res.status_code, 200)

        # POST edit
        valid_date = (date.today() + timedelta(days=10)).isoformat()
        res = self.client.post(reverse('job_edit', args=[self.job.id]), {
            'job_title': 'Senior Web Designer Needed',
            'description': 'Updated description',
            'location': 'Kochi',
            'required_skills': 'React, Figma',
            'work_date': valid_date,
            'work_duration': '4 Hours'
        })
        self.assertEqual(res.status_code, 302)
        self.job.refresh_from_db()
        self.assertEqual(self.job.job_title, 'Senior Web Designer Needed')

        # DELETE job
        res = self.client.get(reverse('job_delete', args=[self.job.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_applicants_for_job(self):
        self.client.login(username='cust@example.com', password='password123')
        res = self.client.get(reverse('applicants_for_job', args=[self.job.id]))
        self.assertEqual(res.status_code, 302) # Redirects to applicant selection for the first application

    def test_applicant_selection_get_and_post_actions(self):
        self.client.login(username='cust@example.com', password='password123')
        
        # GET applicant selection
        res = self.client.get(reverse('applicant_selection', args=[self.application.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Student Worker')
        self.assertContains(res, 'E-Commerce Prototype')

        # POST shortlist
        res = self.client.post(reverse('applicant_selection', args=[self.application.id]), {'action': 'shortlist'})
        self.assertEqual(res.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Shortlisted')
        self.assertTrue(Notification.objects.filter(student=self.student_profile, message__contains='shortlisted').exists())

        # POST hire/accept
        res = self.client.post(reverse('applicant_selection', args=[self.application.id]), {'action': 'hire'})
        self.assertEqual(res.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Accepted')
        self.assertTrue(Notification.objects.filter(student=self.student_profile, message__contains='accepted').exists())

        # POST reject
        res = self.client.post(reverse('applicant_selection', args=[self.application.id]), {'action': 'reject'})
        self.assertEqual(res.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Rejected')

    def test_manage_application_actions(self):
        self.client.login(username='cust@example.com', password='password123')
        
        # Action shortlist
        res = self.client.post(reverse('manage_application', args=[self.application.id, 'shortlist']))
        self.assertEqual(res.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Shortlisted')

        # Action accept
        res = self.client.post(reverse('manage_application', args=[self.application.id, 'accept']))
        self.assertEqual(res.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Accepted')

    def test_work_completion_and_rating_review_flow(self):
        self.client.login(username='cust@example.com', password='password123')
        
        # Mark work completed with valid date
        today_str = date.today().isoformat()
        res = self.client.post(reverse('work_completion', args=[self.application.id]), {
            'completion_date': today_str,
            'work_status': 'Completed',
            'remarks': 'Fantastic job performed by the student.'
        })
        self.assertEqual(res.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Completed')

        # Verify WorkCompletion object
        wc = WorkCompletion.objects.filter(application=self.application).first()
        self.assertIsNotNone(wc)
        self.assertEqual(wc.work_status, 'Completed')
        self.assertEqual(wc.job, self.job)

        # GET rating review page
        res = self.client.get(reverse('rating_review', args=[self.application.id]))
        self.assertEqual(res.status_code, 200)

        # POST rating & review
        res = self.client.post(reverse('rating_review', args=[self.application.id]), {
            'rating': '5',
            'review_comment': 'Outstanding performance and communication!'
        })
        self.assertEqual(res.status_code, 302)

        # Verify Review object
        review = Review.objects.filter(application=self.application).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.student, self.student_user)
        self.assertEqual(review.customer, self.customer_user)
        self.assertEqual(review.job, self.job)

        # Test updating existing review
        res = self.client.post(reverse('rating_review', args=[self.application.id]), {
            'rating': '4',
            'review_comment': 'Updated: Good communication and solid output overall.'
        })
        self.assertEqual(res.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)
        self.assertEqual(Review.objects.filter(application=self.application).count(), 1)
