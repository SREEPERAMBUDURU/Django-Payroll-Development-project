# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, LeaveRequest
from django.forms.widgets import DateInput,TextInput
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator 
from django import forms
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import password_validation
from .models import User 
from django.contrib.auth import get_user_model

class EmployeeRegistrationForm(UserCreationForm):

    full_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=10,
        validators=[MaxLengthValidator(10)],
        help_text='')
    class Meta:
        model = User
        fields = ('username','full_name', 'password1', 'password2', 'email','phone_number', 'position')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("<br>This email address is already in use. Please use a different email.")
        return email
 
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if len(phone_number) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits long.')
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employee = True
        if commit:
            user.save()
        return user

class HrRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    phone_number = forms.CharField(
        max_length=10,
        validators=[MaxLengthValidator(10)],
        help_text='')

    class Meta:
        model = User
        fields = ('username', 'full_name', 'password1', 'password2','phone_number', 'email')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("<br>This email address is already in use. Please use a different email.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if len(phone_number) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits long.')
        return phone_number
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''


    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_hr = True
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    pass

class LeaveRequestForm(forms.ModelForm):
    LEAVE_TYPES = [
        ('Casual Leave', 'Casual Leave'),
        ('Medical Leave', 'Medical Leave'),
        ('Earned Leave', 'Earned Leave (EL) or Privileged Leave (PL)'),
        ('Leave Without Pay', 'Leave Without Pay (LWP)'),
    ]

    leave_type = forms.ChoiceField(choices=LEAVE_TYPES, required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'leave_type', 'description', 'hr']
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter choices for hr field to show only HR users
        self.fields['hr'].queryset = User.objects.filter(is_hr=True)
        self.fields['hr'].label_from_instance = lambda obj: f"{obj.username} (HR)" if obj.is_hr else obj.username
        self.fields['hr'].empty_label = "Select HR"


        self.fields['leave_count'] = forms.IntegerField(label='Paid Leave Count', initial=15, disabled=True)

    def leaves_taken(self, user):
        return LeaveRequest.objects.filter(employee=user, is_approved=True).count()






User = get_user_model()

class UserUpdateForm(UserChangeForm):
    full_name = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=10, validators=[MaxLengthValidator(10)], required=True)
    old_password = forms.CharField(label='Old Password', widget=forms.PasswordInput, required=False)
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'old_password', 'new_password1', 'new_password2']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit() or len(phone_number) != 10:
            raise forms.ValidationError("Phone Number must be exactly 10 digits long.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if (new_password1 or new_password2) and not old_password:
            self.add_error('old_password', "Please enter your old password to change it.")
        elif old_password and (not new_password1 or not new_password2):
            self.add_error('new_password1', "Please enter a new password and confirm it.")
        elif new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "The two new password fields didn't match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        old_password = self.cleaned_data.get('old_password')
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')

        if old_password and new_password1 and new_password2:
            if user.check_password(old_password):
                if new_password1 == new_password2:
                    user.set_password(new_password1)
                else:
                    raise forms.ValidationError("The two new password fields didn't match.")
            else:
                raise forms.ValidationError("Your old password was entered incorrectly. Please enter it again.")
        
        if commit:
            user.save()
        return user
