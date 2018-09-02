from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView

import AppFXReturns.views as views

urlpatterns = [
    url(r'^get_date_range/', views.get_date_range),
    url(r'^gen_report/', views.gen_report),
    url(r'^show_data/', views.show_data),
    url(r'^', views.index),
]