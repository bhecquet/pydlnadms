from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'pydlnadms_frontend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^frontend/', include('frontend.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
