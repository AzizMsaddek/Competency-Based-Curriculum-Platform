from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='fileup'),
    path('process/', views.process, name='process'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('process_data_ajax/', views.process_data_ajax, name='process_data_ajax'),
    path('dashboard/', views.dashboard, name='dashboard'),

]
