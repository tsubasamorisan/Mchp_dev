from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^profile/', include('user_profile.urls')),
    url(r'^school/', include('schedule.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/settings', 'user_profile.views.account_settings', name='account_settings'),
    url(r'^classes/', 'schedule.views.classes', name='classes'),
    url(r'^documents/', include('documents.urls')),
    url(r'^dashboard/', include('dashboard.urls')),
    url('^\u262d', 'landing.views.party'),
    url(r'^$', include('landing.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
