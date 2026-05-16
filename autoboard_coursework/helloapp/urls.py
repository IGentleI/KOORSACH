from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .forms import LoginForm

app_name = 'helloapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('fallback-car-image/<str:brand>/<str:model>/<int:seed>.svg', views.car_image_fallback, name='car_image_fallback'),

    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('login/', auth_views.LoginView.as_view(template_name='helloapp/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/become-seller/', views.become_seller, name='become_seller'),

    # Старые адреса сохранены, чтобы проект был похож на исходную заготовку.
    path('add/', views.car_ad_form, name='car_ad_form'),
    path('list/', views.car_ad_list, name='car_ad_list'),
    path('detail/<int:pk>/', views.car_ad_detail, name='car_ad_detail'),
    path('edit/<int:pk>/', views.car_ad_edit, name='car_ad_edit'),
    path('delete/<int:pk>/', views.car_ad_delete, name='car_ad_delete'),

    # Более понятные адреса для защиты курсовой.
    path('ads/', views.car_ad_list, name='ads'),
    path('ads/add/', views.car_ad_form, name='ad_add'),
    path('ads/<int:pk>/', views.car_ad_detail, name='ad_detail'),
    path('ads/<int:pk>/edit/', views.car_ad_edit, name='ad_edit'),
    path('ads/<int:pk>/delete/', views.car_ad_delete, name='ad_delete'),
    path('ads/<int:pk>/favorite/', views.favorite_toggle, name='favorite_toggle'),
    path('ads/<int:pk>/contact/', views.contact_seller, name='contact_seller'),

    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/<int:pk>/<str:status>/', views.moderation_update, name='moderation_update'),

    path('ajax/check-phone/', views.ajax_check_phone, name='ajax_check_phone'),
    path('ajax/check-email/', views.ajax_check_email, name='ajax_check_email'),
    path('ajax/car-ad-stats/', views.ajax_car_ad_stats, name='ajax_car_ad_stats'),
    path('ajax/latest-car-ads/', views.ajax_latest_car_ads, name='ajax_latest_car_ads'),
]
