from django import forms
from .models import CustomUser, Portfolio, Place, KERALA_DISTRICTS
from students.models import Student
from .validators import (
    validate_image_file,
    validate_document_file,
    validate_verification_doc,
    validate_portfolio_image,
    validate_video_file,
    validate_mobile_number,
)


class StudentRegistrationForm(forms.ModelForm):
    fullname = forms.CharField(required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    place = forms.CharField(required=True, label="City / Place")
    password = forms.CharField(widget=forms.PasswordInput(), required=True, min_length=6)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=True, min_length=6)

    class Meta:
        model = Student
        fields = [
            'mobile',
            'college',
            'course',
            'semester',
            'address',
            'profile_photo',
            'district',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your residential address'}),
            'mobile': forms.TextInput(attrs={'placeholder': 'e.g. 9876543210'}),
            'college': forms.TextInput(attrs={'placeholder': 'College / University name'}),
            'course': forms.TextInput(attrs={'placeholder': 'e.g. B.Tech Computer Science'}),
            'semester': forms.TextInput(attrs={'placeholder': 'e.g. Semester 6'}),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '').strip()
        if mobile:
            return validate_mobile_number(mobile)
        return mobile

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            validate_image_file(photo)
        return photo

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password != confirm:
            raise forms.ValidationError("Passwords do not match.")

        email = cleaned_data.get("email")
        if email:
            if CustomUser.objects.filter(username=email).exists() or CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError("A user with this email already exists.")

        district = cleaned_data.get('district')
        place_name = cleaned_data.get('place')
        if district and place_name:
            place_obj, created = Place.objects.get_or_create(
                name=place_name.strip(),
                district=district
            )
            cleaned_data['place_obj'] = place_obj

        return cleaned_data


class StudentVerificationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['college_id']
        widgets = {
            'college_id': forms.FileInput(attrs={'accept': '.pdf,image/*', 'class': 'form-control'})
        }

    def clean_college_id(self):
        college_id = self.cleaned_data.get('college_id')
        if college_id:
            validate_verification_doc(college_id)
        return college_id


class StudentProfileForm(forms.ModelForm):
    place_name = forms.CharField(
        required=False,
        label="Place / City",
        widget=forms.TextInput(attrs={'placeholder': 'City / Town / Place', 'class': 'form-input'})
    )

    class Meta:
        model = Student
        fields = [
            'full_name',
            'mobile',
            'college',
            'course',
            'semester',
            'district',
            'address',
            'profile_photo',
            'skills',
            'education',
            'experience',
            'resume',
            'about_me',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Your Full Name', 'class': 'form-input'}),
            'mobile': forms.TextInput(attrs={'placeholder': 'Contact phone number (e.g. 9876543210)', 'class': 'form-input'}),
            'college': forms.TextInput(attrs={'placeholder': 'College name', 'class': 'form-input'}),
            'course': forms.TextInput(attrs={'placeholder': 'Degree / Course', 'class': 'form-input'}),
            'semester': forms.TextInput(attrs={'placeholder': 'e.g. Sem 4', 'class': 'form-input'}),
            'district': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Address', 'class': 'form-textarea'}),
            'skills': forms.TextInput(attrs={'placeholder': 'e.g. Python, UI/UX Design, Event Management, Photography', 'class': 'form-input'}),
            'education': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Educational background, certificates, high school, university details...', 'class': 'form-textarea'}),
            'experience': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Previous internships, freelance projects, club roles, part-time jobs...', 'class': 'form-textarea'}),
            'about_me': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief summary of who you are, your passions, reliability, and work ethic...', 'class': 'form-textarea'}),
            'profile_photo': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-file-input'}),
            'resume': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx', 'class': 'form-file-input'}),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '').strip()
        if mobile:
            return validate_mobile_number(mobile)
        return mobile

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            validate_image_file(photo)
        return photo

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            validate_document_file(resume)
        return resume

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.place:
            self.fields['place_name'].initial = self.instance.place.name

    def save(self, commit=True):
        student = super().save(commit=False)
        place_name = self.cleaned_data.get('place_name', '').strip()
        district = self.cleaned_data.get('district')
        if place_name and district:
            place_obj, _ = Place.objects.get_or_create(name=place_name, district=district)
            student.place = place_obj
        elif place_name and not district:
            place_obj = Place.objects.filter(name__iexact=place_name).first()
            if not place_obj:
                place_obj = Place.objects.create(name=place_name, district='Ernakulam')
            student.place = place_obj
        elif not place_name:
            student.place = None

        if commit:
            student.save()
            # Also keep user's first_name in sync with full_name if available
            if student.user and student.full_name:
                student.user.first_name = student.full_name.split()[0] if student.full_name else ''
                student.user.save(update_fields=['first_name'])

        return student


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = [
            'work_title',
            'description',
            'photo',
            'reel'
        ]
        widgets = {
            'work_title': forms.TextInput(attrs={
                'placeholder': 'Project / Work Title (e.g. Brand Identity Design, Cafe Promotional Reel)',
                'class': 'form-input',
                'id': 'portfolio_work_title'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Explain what you created, tools used, and the impact or result...',
                'class': 'form-textarea',
                'id': 'portfolio_description'
            }),
            'photo': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-file-input',
                'id': 'portfolio_photo'
            }),
            'reel': forms.FileInput(attrs={
                'accept': 'video/*',
                'class': 'form-file-input',
                'id': 'portfolio_reel'
            }),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            validate_portfolio_image(photo)
        return photo

    def clean_reel(self):
        reel = self.cleaned_data.get('reel')
        if reel:
            validate_video_file(reel)
        return reel

    def clean_work_title(self):
        title = self.cleaned_data.get('work_title', '').strip()
        if not title:
            raise forms.ValidationError("Project title is required.")
        return title



# =========================================================
# ADMIN MANAGEMENT FORMS
# =========================================================

from jobs.models import Job
from customers.models import Customer
from .models import Report


class AdminUserCreationForm(forms.Form):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('customer', 'Customer (Employer)'),
        ('admin', 'Admin / Staff'),
    )

    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, initial='student', widget=forms.Select(attrs={'class': 'form-select', 'id': 'create_user_type'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Unique username or email'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'user@example.com'}))
    full_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Min 6 characters'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm password'}))
    mobile = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone number'}))
    
    # Student specific
    college = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'College / Institute'}))
    course = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Course / Department'}))
    semester = forms.CharField(required=False, max_length=50, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. S4'}))
    district = forms.ChoiceField(required=False, choices=[('', '-- Select District --')] + KERALA_DISTRICTS, widget=forms.Select(attrs={'class': 'form-select'}))
    place = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City / Town'}))
    is_verified = forms.BooleanField(required=False, initial=False, label="Mark Student Verified Immediately", widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    is_active = forms.BooleanField(required=False, initial=True, label="Active Account", widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '').strip()
        if mobile:
            return validate_mobile_number(mobile)
        return mobile

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")

        return cleaned_data


    def save(self):
        cd = self.cleaned_data
        user_type = cd['user_type']
        is_staff = (user_type == 'admin')
        is_superuser = (user_type == 'admin')

        user = CustomUser.objects.create_user(
            username=cd['username'],
            email=cd['email'],
            password=cd['password'],
            user_type=user_type,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=cd.get('is_active', True)
        )

        if user_type == 'student':
            place_obj = None
            if cd.get('district') and cd.get('place'):
                place_obj, _ = Place.objects.get_or_create(
                    name=cd['place'].strip(),
                    district=cd['district']
                )
            Student.objects.create(
                user=user,
                full_name=cd['full_name'],
                mobile=cd.get('mobile', ''),
                college=cd.get('college', ''),
                course=cd.get('course', ''),
                semester=cd.get('semester', ''),
                district=cd.get('district', ''),
                place=place_obj,
                is_verified=cd.get('is_verified', False)
            )
        elif user_type == 'customer':
            Customer.objects.create(
                user=user,
                full_name=cd['full_name'],
                email=cd['email'],
                mobile_number=cd.get('mobile', ''),
            )

        return user


class AdminUserEditForm(forms.Form):
    full_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    mobile = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-input'}))
    is_active = forms.BooleanField(required=False, label="Active Account", widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    
    # Student specific
    college = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    course = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    semester = forms.CharField(required=False, max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    district = forms.ChoiceField(required=False, choices=[('', '-- Select District --')] + KERALA_DISTRICTS, widget=forms.Select(attrs={'class': 'form-select'}))
    place = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    is_verified = forms.BooleanField(required=False, label="Verified Student", widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    is_rejected = forms.BooleanField(required=False, label="Rejected Verification", widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}))

    def __init__(self, *args, user_obj=None, **kwargs):
        self.user_obj = user_obj
        super().__init__(*args, **kwargs)

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '').strip()
        if mobile:
            return validate_mobile_number(mobile)
        return mobile

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if self.user_obj:
            existing = CustomUser.objects.filter(email=email).exclude(id=self.user_obj.id)
            if existing.exists():
                raise forms.ValidationError("Another user already has this email address.")
        return email



class AdminJobEditForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'job_title',
            'customer',
            'location',
            'required_skills',
            'work_date',
            'work_duration',
            'description',
        ]
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Job Title'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Location / City'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Python, Photography, Event Support'}),
            'work_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'work_duration': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea', 'placeholder': 'Job description and requirements...'}),
        }

    def clean_job_title(self):
        title = self.cleaned_data.get('job_title', '').strip()
        if not title:
            raise forms.ValidationError("Job title cannot be blank.")
        return title


class ReportCreationForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            'report_type',
            'reported_user',
            'reported_job',
            'reported_review',
            'reason',
            'description'
        ]
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'reported_user': forms.Select(attrs={'class': 'form-select'}),
            'reported_job': forms.Select(attrs={'class': 'form-select'}),
            'reported_review': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea', 'placeholder': 'Describe the issue or violation in detail...'}),
        }


class ReportResolutionForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['status', 'action_taken', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'action_taken': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea', 'placeholder': 'Enter admin resolution comments or internal audit notes...'}),
        }