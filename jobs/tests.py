import datetime
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from students.models import Student
from jobs.models import Job, JobApplication
from customers.models import Review


class JobApplicationViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.customer = CustomUser.objects.create_user(
            username='employer1@example.com',
            email='employer1@example.com',
            password='password123',
            user_type='customer'
        )

        self.student = CustomUser.objects.create_user(
            username='student1@example.com',
            email='student1@example.com',
            password='password123',
            user_type='student'
        )
        self.student_profile = Student.objects.create(
            user=self.student,
            full_name='Alice Student',
            is_verified=True
        )

        today = datetime.date.today()
        self.job1 = Job.objects.create(
            customer=self.customer,
            job_title='Python Developer',
            description='Build Django web application',
            location='Kochi',
            required_skills='Python, Django',
            work_date=today + datetime.timedelta(days=7),
            work_duration='1 Week'
        )

        self.job2 = Job.objects.create(
            customer=self.customer,
            job_title='Graphic Designer',
            description='Design marketing banners',
            location='Trivandrum',
            required_skills='Photoshop, Figma',
            work_date=today + datetime.timedelta(days=10),
            work_duration='2 Days'
        )

    def test_job_application_page_loads(self):
        response = self.client.get(reverse('job_application'))
        self.assertEqual(response.status_code, 200)

    def test_available_jobs_page_loads_and_search(self):
        response = self.client.get(reverse('available_jobs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertContains(response, 'Graphic Designer')

        # Test Search Query
        response = self.client.get(reverse('available_jobs') + '?q=Python')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertNotContains(response, 'Graphic Designer')

        # Test Location Filter
        response = self.client.get(reverse('available_jobs') + '?location=Kochi')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertNotContains(response, 'Graphic Designer')

        # Test Duration Filter
        response = self.client.get(reverse('available_jobs') + '?duration=1+Week')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertNotContains(response, 'Graphic Designer')

    def test_applied_jobs_requires_login(self):
        response = self.client.get(reverse('applied_jobs'))
        self.assertEqual(response.status_code, 302)

    def test_apply_job_get_and_post(self):
        self.client.login(username='student1@example.com', password='password123')
        
        # GET apply job
        response = self.client.get(reverse('apply_job', args=[self.job1.id]))
        self.assertEqual(response.status_code, 200)

        # POST apply job with short cover message (validation fails)
        response = self.client.post(reverse('apply_job', args=[self.job1.id]), {
            'cover_message': 'Short',
            'availability': 'Immediately'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(JobApplication.objects.filter(student=self.student, job=self.job1).exists())

        # POST apply job with valid data
        response = self.client.post(reverse('apply_job', args=[self.job1.id]), {
            'cover_message': 'I have built multiple Django projects and can start right away.',
            'availability': 'Immediately'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(JobApplication.objects.filter(student=self.student, job=self.job1).exists())

        app = JobApplication.objects.get(student=self.student, job=self.job1)
        self.assertEqual(app.status, 'Pending')
        self.assertIn('Alice Student', str(app))

        # Test duplicate application prevention
        response = self.client.get(reverse('apply_job', args=[self.job1.id]))
        self.assertEqual(response.status_code, 302)

    def test_applied_jobs_status_filtering_and_reviews(self):
        self.client.login(username='student1@example.com', password='password123')

        # Create applications
        app1 = JobApplication.objects.create(
            student=self.student,
            job=self.job1,
            cover_message='Cover message with enough length to be valid.',
            availability='Immediately',
            status='Completed'
        )

        Review.objects.create(
            application=app1,
            student=self.student,
            customer=self.customer,
            job=self.job1,
            rating=5,
            review_comment='Exceptional work completed on time!'
        )

        app2 = JobApplication.objects.create(
            student=self.student,
            job=self.job2,
            cover_message='Another cover message for design role.',
            availability='Weekends Only',
            status='Pending'
        )

        # GET applied jobs (all)
        response = self.client.get(reverse('applied_jobs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertContains(response, 'Graphic Designer')
        self.assertContains(response, 'Exceptional work completed on time!')

        # GET filter by Completed
        response = self.client.get(reverse('applied_jobs') + '?status=Completed')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertNotContains(response, 'Graphic Designer')

    def test_job_post_by_customer(self):
        self.client.login(username='employer1@example.com', password='password123')

        response = self.client.get(reverse('job_post'))
        self.assertEqual(response.status_code, 200)

        future_date = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        response = self.client.post(reverse('job_post'), {
            'job_title': 'Content Writer',
            'description': 'Write articles for student blog',
            'location': 'Remote',
            'required_skills': 'Writing, English',
            'work_date': future_date,
            'work_duration': '2 Days'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Job.objects.filter(job_title='Content Writer').exists())

    def test_customer_cannot_apply_for_job(self):
        self.client.login(username='employer1@example.com', password='password123')
        response = self.client.post(reverse('apply_job', args=[self.job1.id]), {
            'cover_message': 'I want to apply but I am an employer',
            'availability': 'Immediately'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(JobApplication.objects.filter(student=self.customer, job=self.job1).exists())

    def test_student_cannot_post_job(self):
        self.client.login(username='student1@example.com', password='password123')
        response = self.client.get(reverse('job_post'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('student_dashboard'))

    def test_job_post_past_date_rejected(self):
        import datetime
        self.client.login(username='employer1@example.com', password='password123')
        past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        response = self.client.post(reverse('job_post'), {
            'job_title': 'Past Date Job',
            'description': 'This job has an invalid date in the past.',
            'location': 'Kochi',
            'required_skills': 'Testing',
            'work_date': past_date,
            'work_duration': '1 Day'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Job.objects.filter(job_title='Past Date Job').exists())

    def test_available_jobs_date_filtering_and_expired_badge(self):
        import datetime
        today = datetime.date.today()
        # Create an expired job directly in DB
        expired_job = Job.objects.create(
            customer=self.customer,
            job_title='Old Festival Helper',
            description='Event helper for past festival',
            location='Kozhikode',
            required_skills='Coordination',
            work_date=today - datetime.timedelta(days=5),
            work_duration='1 Day'
        )

        # GET available jobs
        res = self.client.get(reverse('available_jobs'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Old Festival Helper')
        self.assertContains(res, 'Date Passed')
        self.assertContains(res, 'Date Expired')

        # Filter by upcoming
        res_upcoming = self.client.get(reverse('available_jobs') + '?date_status=upcoming')
        self.assertEqual(res_upcoming.status_code, 200)
        self.assertNotContains(res_upcoming, 'Old Festival Helper')

        # Filter by expired
        res_expired = self.client.get(reverse('available_jobs') + '?date_status=expired')
        self.assertEqual(res_expired.status_code, 200)
        self.assertContains(res_expired, 'Old Festival Helper')

    def test_student_cannot_apply_for_expired_job(self):
        import datetime
        self.client.login(username='student1@example.com', password='password123')
        expired_job = Job.objects.create(
            customer=self.customer,
            job_title='Past Date Project',
            description='Project completed last month',
            location='Kollam',
            work_date=datetime.date.today() - datetime.timedelta(days=10),
            work_duration='2 Days'
        )

        res = self.client.post(reverse('apply_job', args=[expired_job.id]), {
            'cover_message': 'I want to apply to this past job',
            'availability': 'Immediately'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('available_jobs'))
        self.assertFalse(JobApplication.objects.filter(student=self.student, job=expired_job).exists())


