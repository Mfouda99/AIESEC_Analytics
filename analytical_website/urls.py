from django.contrib import admin
from django.urls import path, include
import analytics
import analytics.urls
import expa_data
import expa_data.urls
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(analytics.urls)),
    path('expa/', include(expa_data.urls)),
    path('dashboard/',include(expa_data.urls)),
]+ static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])



