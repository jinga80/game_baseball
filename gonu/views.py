from django.shortcuts import render

# Create your views here.

def index(request):
    """고누놀이 게임 메인 페이지"""
    return render(request, 'gonu/index.html')
