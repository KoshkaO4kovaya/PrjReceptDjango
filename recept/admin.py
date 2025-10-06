from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Recipe, RecipeStep, RecipeIngredient, Review, Favorite,
    Genre, ListIngredient
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    ordering = ['email']
    list_display = ['email', 'full_name', 'phone_num', 'is_staff']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('full_name', 'phone_num', 'birth_date', 'avatar')}),
        ('Права и группы', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_num', 'password', 'password2'),
        }),
    )
    search_fields = ('email', 'full_name', 'phone_num')


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1 


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_public')
    list_filter = ('is_public', 'genres', 'user')
    search_fields = ('title', 'description')
    inlines = [RecipeStepInline, RecipeIngredientInline] 

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'rating', 'created_at')
    list_filter = ('rating',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')
    search_fields = ('user__email', 'recipe__title')


admin.site.register(Genre)
admin.site.register(ListIngredient)
