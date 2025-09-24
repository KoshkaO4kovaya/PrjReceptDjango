from django.shortcuts import render, redirect
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