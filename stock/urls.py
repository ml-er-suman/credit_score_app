from django.urls import path
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('', views.index, name='index'),
    path('test', views.test, name='test'),
    path('predict', views.get_prediction, name='predict'),
    path('login', auth_views.LoginView.as_view(template_name='accounts/login.html')),
    path('logout', auth_views.LogoutView.as_view(template_name= 'accounts/logout.html')),
    # path('enquiry', views.enquiry, name = 'enquiry'),
    # path('prediction', views.prediction, name = 'prediction'),
    # path('predict', views.get_prediction, name = 'predict'),



]