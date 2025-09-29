from django import forms
<<<<<<< HEAD
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, label='ФИО')
    phone_num = forms.CharField(max_length=20, required=True, label='Номер телефона')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Дата рождения')
    email = forms.EmailField(required=True, label='Почта')

    class Meta:
        model = User
        fields = ('full_name', 'phone_num', 'birth_date', 'email', 'password1', 'password2')

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Почта или номер телефона')



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'phone_num', 'birth_date', 'avatar']
=======
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('email', 'name', 'phone_num', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким Email уже существует.')
        return email
>>>>>>> github/main
