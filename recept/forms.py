from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.forms import modelformset_factory, formset_factory, FileInput 
from .models import Recipe, RecipeStep, RecipeIngredient, ListIngredient, Genre
import re

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, label='ФИО')
    phone_num = forms.CharField(max_length=20, required=True, label='Номер телефона')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Дата рождения')
    email = forms.EmailField(required=True, label='Почта')

    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone_num', 'birth_date') 

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 6:
            raise forms.ValidationError('Пароль должен содержать не менее 6 символов.')
        if not re.match(r'^[A-Za-z0-9]+$', password):
            raise forms.ValidationError('Пароль должен содержать только латинские буквы и цифры.')
        return password


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Почта или номер телефона')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'phone_num', 'birth_date', 'avatar']
        widgets = {
            'avatar': FileInput(), 
        }
            

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone_num', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким Email уже существует.')
        return email


class RecipeForm(forms.ModelForm):
    
    status_field = forms.ChoiceField(
        choices=Recipe.STATUS_CHOICES,
        initial='draft',
        widget=forms.HiddenInput(), 
        required=False,
        label='Статус'
    )

    class Meta:
        model = Recipe
        fields = ['title', 'cover_image', 'description', 'portions', 'calories', 'estimated_cost', 'genres', 'video_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'genres': forms.CheckboxSelectMultiple(),
            'cover_image': forms.FileInput(), 
            'video_file': forms.FileInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        status = self.data.get('status_field') 

        if status == 'published':
            # Проверка обязательных полей для публикации
            if not cleaned_data.get('title'):
                self.add_error('title', 'Название обязательно для публикации.')
            if not cleaned_data.get('description'):
                self.add_error('description', 'Описание обязательно для публикации.')
            # Поля с PositiveIntegerField/DecimalField могут быть пустыми, если null=True, 
            # но мы делаем их обязательными для публикации
            if not cleaned_data.get('portions'):
                 self.add_error('portions', 'Количество порций обязательно для публикации.')
            if not cleaned_data.get('calories'):
                 self.add_error('calories', 'Калорийность обязательна для публикации.')
            if not cleaned_data.get('genres') or len(cleaned_data.get('genres')) == 0:
                self.add_error('genres', 'Выберите хотя бы один жанр для публикации.')
        
        
        return cleaned_data

    def save(self, commit=True):

        recipe = super().save(commit=False)
        
        status = self.cleaned_data.get('status_field', 'draft')

        if not status:
             status = self.data.get('status_field', 'draft')
             
        recipe.status = status
        
        if commit:
            recipe.save()
            self.save_m2m() # Сохраняем ManyToMany связи (жанры)
        return recipe


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = ['order', 'description', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

RecipeStepFormSet = modelformset_factory(RecipeStep, form=RecipeStepForm, extra=1, can_delete=True)


class RecipeIngredientForm(forms.Form):
    ingredient_name = forms.CharField(max_length=100, label='Название ингредиента') 
    quantity = forms.DecimalField(max_digits=6, decimal_places=2, label='Количество')
    unit = forms.ChoiceField(choices=[
        ('g', 'Граммы'),
        ('ml', 'Миллилитры'),
        ('pcs', 'Штуки'),
        ('teasp', 'Чайная ложка'),
        ('tablesp', 'Столовая ложка'),
        ('kg', 'Килограммы'),
        ('cup', 'Кружка'),
    ], label='Единица измерения')
