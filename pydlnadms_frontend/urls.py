from django.urls import include, path

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'pydlnadms_frontend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    path(r'frontend/', include('frontend.urls')),
    path('admin/', admin.site.urls),
]
