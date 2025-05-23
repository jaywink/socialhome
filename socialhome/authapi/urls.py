from django.urls import path
from . import views

urlpatterns = [
    path('set-csrf-token', views.set_csrf_token, name='set_csrf_token'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('user', views.user_view, name='user'),
    #path('api/register', views.register, name='register'),
]
