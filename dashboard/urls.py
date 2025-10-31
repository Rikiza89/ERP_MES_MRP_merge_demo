"""
Dashboard App URLs
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('api/production-chart/', views.api_production_chart, name='api_production_chart'),
    path('api/inventory-status/', views.api_inventory_status, name='api_inventory_status'),
    path('api/kpis/', views.api_kpis, name='api_kpis'),
]