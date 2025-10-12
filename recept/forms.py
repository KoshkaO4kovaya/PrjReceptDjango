from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Review
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

# рецепты
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
        
        status = self.data.get('status_field', 'draft') 

        # Валидация для публикации 
        if status == 'pending':
            
            required_fields = {
                'title': 'Название',
                'description': 'Описание',
                'portions': 'Количество порций',
                'calories': 'Калорийность',
                'estimated_cost': 'Примерная стоимость',
            }
            
            for field, label in required_fields.items():
                if not cleaned_data.get(field):
                    self.add_error(field, f'{label} обязательно для публикации.')
            
            has_cover = cleaned_data.get('cover_image') or (self.instance and self.instance.cover_image)
            if not has_cover:
                self.add_error('cover_image', 'Обложка обязательна для публикации.')

            if not cleaned_data.get('genres'):
                self.add_error('genres', 'Выберите хотя бы один жанр для публикации.')

                

        elif status == 'draft' or status == 'rejected':
            
            simple_fields = ['title', 'description']
            
            has_simple_field_data = any(cleaned_data.get(f) for f in simple_fields)

            if not has_simple_field_data:
                has_file_data = bool(self.files.get('cover_image') or self.files.get('video_file'))
                if self.instance:
                    has_file_data = has_file_data or bool(self.instance.cover_image or self.instance.video_file)
                
                has_m2m_data = bool(cleaned_data.get('genres'))

                if not (has_simple_field_data or has_file_data or has_m2m_data):
                     if not cleaned_data.get('title'):

                        self.add_error(None, 'Для сохранения в черновик заполните хотя бы Название, чтобы рецепт не был пустым.')
        
        return cleaned_data

    def save(self, commit=True):

        recipe = super().save(commit=False)
        
        status = self.data.get('status_field', 'draft') 

        if status == 'pending' and recipe.moderation_notes:
            recipe.moderation_notes = None

        recipe.status = status
        
        if commit:
            recipe.save()
            self.save_m2m() 
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

# админка
class AdminUserEditForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_num', 'birth_date', 'avatar', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'email': 'Email',
            'full_name': 'Полное имя',
            'phone_num': 'Номер телефона',
            'birth_date': 'Дата рождения',
            'avatar': 'Аватар',
            'is_active': 'Активен (Может войти)',
            'is_staff': 'Персонал (Доступ к админке Django)',
            'is_superuser': 'Суперпользователь (Полный доступ)',
        }

# отзывы

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Поделитесь своим мнением о рецепте...'})
        }
        labels = {
            'comment': 'Комментарий',
        }
