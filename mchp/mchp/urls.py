from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^profile/', include('user_profile.urls')),
    url(r'^school/', include('schedule.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/settings', 'user_profile.views.account_settings', name='account_settings'),
    url(r'^calendar/', include('calendar_mchp.urls')),
    url(r'^classes/', 'schedule.views.classes', name='classes'),
    url(r'^documents/', include('documents.urls')),
    url(r'^home/', include('dashboard.urls')),
    url(r'^notification/', include('notification.urls')),
    url(r'^referral/', include('referral.urls')),
    url(r'^payment/', include('payment.urls')),
    url('^\u262d', 'landing.views.party'),

    url(r'^privacy-policy/$', 'lib.views.privacy_policy', name='privacy_policy'),
    url(r'^help/$', 'lib.views.help', name='help'),

    url(r'^$', include('landing.urls')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/lib/img/favicon.ico')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += patterns('django.contrib.flatpages.views',
    url(r'^about-us/$', 'flatpage', {'url': '/about-us/'}, name='about'),
)
