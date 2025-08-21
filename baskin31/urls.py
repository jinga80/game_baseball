from django.urls import path
from . import views

app_name = 'baskin31'

urlpatterns = [
    path('', views.index, name='index'),
]
