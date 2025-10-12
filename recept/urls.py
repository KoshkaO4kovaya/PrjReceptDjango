from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import signup_view, login_view, profile_view, admin_profile_view, logout_view, profile_edit_view, recipe_detail_view,toggle_favorite, user_profile_view

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile_edit/', profile_edit_view, name='profile_edit'),
    path('admin-profile/', admin_profile_view, name='admin_profile'),
    path('recipes/create/', views.recipe_create_view, name='recipe_create'),
    path('recipes/<int:pk>/edit/', views.recipe_edit_view, name='recipe_edit'),
    path('recipes/<int:pk>/', views.recipe_detail_view, name='recipe_detail'), 
    path('recipes/<int:pk>/delete/', views.recipe_delete_view, name='recipe_delete'),
    path('recipes/<int:pk>/reviews/', views.recipe_reviews_view, name='recipe_reviews'),
    path('users/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('favorite/toggle/<int:recipe_id>/', views.toggle_favorite, name='toggle_favorite'), 
    path('recipes/', views.recipe_list_view, name='recipe_list'), 
    path('favorites/', views.favorite_recipes_view, name='favorite_recipes'),
    # админка
    path('admin-profile/', views.admin_profile_view, name='admin_profile'),
    path('admin-users/', views.admin_users_list_view, name='admin_users_list'),
    path('admin-recipes/', views.admin_recipes_list_view, name='admin_recipes_list'),
    path('recipes/<int:pk>/edit-genres/', views.admin_edit_recipe_genres, name='admin_edit_recipe_genres'),
    path('admin/genres/add/', views.admin_add_genre, name='admin_add_genre'),
    path('admin/users/<int:pk>/view/', views.admin_user_detail_view, name='admin_user_detail'),
    path('admin/users/<int:pk>/edit/', views.admin_user_edit_view, name='admin_user_edit'),
    path('admin/users/<int:pk>/delete/', views.admin_user_delete_view, name='admin_user_delete'),
    path('admin-moderation/', views.admin_moderation_list_view, name='admin_moderation_list'),
    path('admin-moderation/<int:pk>/approve/', views.admin_approve_recipe_view, name='admin_approve_recipe'),
    path('admin-moderation/<int:pk>/reject/', views.admin_reject_recipe_view, name='admin_reject_recipe'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)