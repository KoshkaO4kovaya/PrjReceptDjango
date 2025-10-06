from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_num = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='user_avatars/', blank=True, null=True, help_text='Аватар пользователя')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ListIngredient(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
    ]
     
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', help_text='Статус рецепта: черновик или опубликован')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    title = models.CharField(max_length=200)
    cover_image = models.ImageField(upload_to='recipe_images/', blank=True, null=True, help_text='Обложка рецепта')
    description = models.TextField()
    portions = models.PositiveIntegerField(default=1)
    calories = models.PositiveIntegerField(help_text='Калорийность на порцию')
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name='recipes', blank=True)  
    ingredients = models.ManyToManyField(ListIngredient, through='RecipeIngredient', related_name='recipes')
    video_file = models.FileField(upload_to='recipe_videos/', blank=True, null=True, help_text='Видео рецепт (файл)')
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)




class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveIntegerField(help_text='Порядок шага')
    description = models.TextField(blank=True, null=True, help_text='Текстовое описание шага')
    image = models.ImageField(upload_to='recipe_steps/', blank=True, null=True, help_text='Картинка к шагу')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.recipe.title} - шаг {self.order}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(ListIngredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, help_text='Количество ингредиента')
    unit = models.CharField(max_length=8, choices=[
        ('g', 'Граммы'),
        ('ml', 'Миллилитры'),
        ('pcs', 'Штуки'),
        ('teasp', 'Чайная ложка'),
        ('tablesp', 'Столовая ложка'),
        ('kg', 'Килограммы'),
        ('cup', 'Кружка'),
    ])

    def __str__(self):
        return f'{self.quantity} {self.get_unit_display()} {self.ingredient.name}'


class Review(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.PositiveSmallIntegerField(default=0) 
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('recipe', 'user')

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')