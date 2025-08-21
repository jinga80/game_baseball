from django.urls import path
from . import views

app_name = 'gonu'

urlpatterns = [
    path('', views.index, name='index'),
]
