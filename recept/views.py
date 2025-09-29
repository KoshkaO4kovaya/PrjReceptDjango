from django.shortcuts import render, redirect
<<<<<<< HEAD
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import User


def index(request): 
    return render(request, 'index.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.full_name = form.cleaned_data['full_name']
            user.phone_num = form.cleaned_data['phone_num']
            user.birth_date = form.cleaned_data['birth_date']
            user.save()
            login(request, user)
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email_or_phone = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = None
            try:
                # сначала по email
                user_obj = User.objects.get(email=email_or_phone)
                user = authenticate(request, email=user_obj.email, password=password)
            except User.DoesNotExist:
                try:
                    user_obj = User.objects.get(phone_num=email_or_phone)
                    user = authenticate(request, email=user_obj.email, password=password)
                except User.DoesNotExist:
                    user = None
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect('admin_profile')
                return redirect('profile')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def profile_view(request):
    if request.user.is_superuser:
        return redirect('admin_profile')
    return render(request, 'profile.html')

@login_required
def admin_profile_view(request):
    if not request.user.is_superuser:
        return redirect('profile')
    return render(request, 'admin_profile.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # или на страницу профиля
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'profile_edit.html', {'form': form})
=======
from django.contrib.auth import login
from .forms import RegistrationForm

def index(request):
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # авторизация после регистрации
            return redirect('home')  # заменить на нужный url или имя пути
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})
>>>>>>> github/main
