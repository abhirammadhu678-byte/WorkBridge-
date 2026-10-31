from django import forms
from .models import Job, JobApplication

class JobPostForm(forms.ModelForm):

    class Meta:
        model = Job

        fields = [
            'job_title',
            'description',
            'location',
            'required_skills',
            'work_date',
            'work_duration'
        ]

        widgets = {
            'job_title': forms.TextInput(attrs={
                'placeholder': 'Enter Job Title'
            }),

            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the work'
            }),

            'location': forms.TextInput(attrs={
                'placeholder': 'Location'
            }),

            'required_skills': forms.TextInput(attrs={
                'placeholder': 'Python, Communication'
            }),

            'work_date': forms.DateInput(attrs={
                'type': 'date'
            }),

            'work_duration': forms.TextInput(attrs={
                'placeholder': 'Example: 5 Hours'
            }),
        }

    def clean_job_title(self):
        title = self.cleaned_data.get('job_title', '').strip()
        if not title:
            raise forms.ValidationError("Job title cannot be empty.")
        if len(title) < 3:
            raise forms.ValidationError("Job title must be at least 3 characters long.")
        return title

    def clean_location(self):
        loc = self.cleaned_data.get('location', '').strip()
        if not loc:
            raise forms.ValidationError("Location is required.")
        return loc

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if not desc:
            raise forms.ValidationError("Job description is required.")
        if len(desc) < 10:
            raise forms.ValidationError("Please provide a more descriptive job summary (min 10 characters).")
        return desc

    def clean_work_date(self):
        from datetime import date
        work_date = self.cleaned_data.get('work_date')
        if work_date and work_date < date.today():
            raise forms.ValidationError("Work date cannot be in the past.")
        return work_date



class JobApplicationForm(forms.ModelForm):

    class Meta:
        model = JobApplication

        fields = [
            'cover_message',
            'availability'
        ]

        widgets = {
            'cover_message': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Explain why you are a great fit for this role, your relevant skills/experience, and what value you bring...',
                'id': 'cover_message',
                'class': 'form-input form-textarea'
            }),

            'availability': forms.TextInput(attrs={
                'placeholder': 'e.g. Immediately, Weekends, Full-time, 4 PM - 8 PM',
                'id': 'availability',
                'class': 'form-input'
            })
        }

    def clean_cover_message(self):
        cover_message = self.cleaned_data.get('cover_message', '').strip()
        if not cover_message:
            raise forms.ValidationError("Cover message is required.")
        if len(cover_message) < 15:
            raise forms.ValidationError(f"Cover message must be at least 15 characters long (currently {len(cover_message)}).")
        if len(cover_message) > 2000:
            raise forms.ValidationError("Cover message cannot exceed 2000 characters.")
        return cover_message

    def clean_availability(self):
        availability = self.cleaned_data.get('availability', '').strip()
        if not availability:
            raise forms.ValidationError("Please provide your availability.")
        if len(availability) < 2:
            raise forms.ValidationError("Please provide a valid availability description.")
        return availability