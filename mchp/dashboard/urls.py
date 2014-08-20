from django.conf.urls import patterns, url

from dashboard import views

urlpatterns = patterns('',
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^feed/', views.feed, name='dashboard_feed'),
    url(r'^toggle-rss/', views.toggle_rss, name='toggle_rss'),
)
