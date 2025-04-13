from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('analytics_OGX/', views.index, name='analytics'),
    path('analytics_ICX/', views.ICX, name='analytics'),
    path('get_ogv_funnel/', views.get_ogv_funnel, name='get_ogv_funnel'),
    path('get_ogta_funnel/', views.get_ogta_funnel, name='get_ogta_funnel'),
    path('get_ogte_funnel/', views.get_ogte_funnel, name='get_ogte_funnel'),
    path('get_igv_funnel/', views.get_igv_funnel, name='get_igv_funnel'),
    path('get_igta_funnel/', views.get_igta_funnel, name='get_igta_funnel'),
    path("get_igv_timeline/", views.get_igv_timeline, name="get_igv_timeline"),
    path("get_igta_timeline/", views.get_igta_timeline, name="get_igta_timeline"),
    path("get_ogv_timeline/", views.get_ogv_timeline, name="get_ogv_timeline"),
    path('get_ogta_timeline/', views.get_ogta_timeline, name='get_ogta_timeline'),
    path('get_ogte_timeline/', views.get_ogte_timeline, name='get_ogte_timeline'),
    path('ogv_process_times/', views.get_ogv_process_times, name='ogv_process_times'),
    path('ogta_process_times/', views.get_ogta_process_times, name='ogta_process_times'),
    path('ogte_process_times/', views.get_ogte_process_times, name='ogte_process_times'),
    path('igv_process_times/', views.get_igv_process_times, name='igv_process_times'),
    path('igta_process_times/', views.get_igta_process_times, name='igta_process_times'),
    path("get_igv_slots_data/", views.get_igv_slots_data, name="get_igv_slots"),  # Add this line
    path("get_igta_slots_data/", views.get_igta_slots_data, name="get_igta_slots"),
    


]
