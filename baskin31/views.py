from django.shortcuts import render

def index(request):
    """배스킨라빈스31 게임 메인 페이지"""
    return render(request, 'baskin31/index.html')
