"""demo_django1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from view.login_view import send_code
from view.login_view import login
from view.login_view import register
from view.image_detect_view import image_detect
from view.viedo_detect_viedo import upload_viedo
from view.viedo_detect_viedo import play_viedo
from view.camara_detect import start_camera
urlpatterns = [
    path('admin/', admin.site.urls),
    path('sendCode/', send_code),

    path('login/', login),
    path('register/', register),
    path('image_detect/',image_detect),
    path('upload_viedo/', upload_viedo),
    path('viedo_detect/', play_viedo),
    path('start_camera/', start_camera),
]
