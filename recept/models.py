from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
     name = models.CharField(max_length=150,
                            help_text='имя пользователя',
                            verbose_name='Введителя имя пользователя')
     email = models.EmailField(unique=True)
     phone_num = models.CharField(max_length=20, blank=True, null=True)
     password_hash = models.CharField(max_length=128)
     created_at = models.DateTimeField(auto_now_add=True)

     def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

     def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

     def __str__(self):
        return self.name
     

class MealType(models.TextChoices):
    BREAKFAST = 'breakfast', 'Завтрак'
    LUNCH = 'lunch', 'Обед'
    DINNER = 'dinner', 'Ужин'


class MainIngredient(models.Model):
    UNIT_CHOICES = [
        ('g', 'Граммы'),
        ('ml', 'Миллилитры'),
        ('pcs', 'Штуки'),
    ]

    name = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default='pcs', help_text='Единица измерения')

    def __str__(self):
        return self.name
    

class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    title = models.CharField(max_length=200)
    cover_image = models.ImageField(upload_to='recipe_images/', blank=True, null=True, help_text='Обложка рецепта')
    description = models.TextField()
    portions = models.PositiveIntegerField(default=1)
    calories = models.PositiveIntegerField(help_text='Калорийность на порцию')
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    meal_type = models.CharField(max_length=20, choices=MealType.choices)
    main_ingredients = models.ManyToManyField(MainIngredient, related_name='recipes')
    video_file = models.FileField(upload_to='recipe_videos/', blank=True, null=True, help_text='Видео рецепт (файл)')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

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
    ingredient = models.ForeignKey(MainIngredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, help_text='Количество ингредиента')

    def __str__(self):
        return f'{self.quantity} {self.ingredient.get_unit_display()} {self.ingredient.name}'   

class Review(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.PositiveSmallIntegerField(default=0)  # рейтинг 0-5
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