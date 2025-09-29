from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import signup_view, login_view, profile_view, admin_profile_view, logout_view, profile_edit_view

urlpatterns = [
    path('', views.index, name='index'),
     path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile_edit/', profile_edit_view, name='profile_edit'),
    path('admin-profile/', admin_profile_view, name='admin_profile'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)