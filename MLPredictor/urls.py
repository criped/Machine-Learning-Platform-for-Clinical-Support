
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [      
    url(r'^admin/', admin.site.urls),
    url(r'^MLPredictorPlatform/', include('MLPredictorPlatform.urls')),
    url(r'^', include('MLPredictorPlatform.urls')),

]