from django.urls import path
from . import views
from .views import funnel_dashboard


urlpatterns = [
    path('sync/', views.sync_expa_data, name='sync_expa_data'),
    path('', funnel_dashboard, name='funnel_dashboard'),
    path('sync_signup_people/', views.sync_signup_people, name='sync_signup_people'),
     path('sync_opportunities/', views.sync_expa_opportunities, name='sync_signup_people'),


]
