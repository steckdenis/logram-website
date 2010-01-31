# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('',
    # Example:
    # (r'^pyv4/', include('pyv4.foo.urls')),
    
    (r'^$', 'pyv4.general.views.index'),
    (r'^ajax-preview.html$', 'pyv4.general.views.ajax_preview'),
    (r'^ajax-preview-pastebin-(?P<format>.+)\.html$', 'pyv4.general.views.ajax_preview_pastebin'),
    (r'^forum\.html$', 'pyv4.forum.views.index'),
    (r'^wiki\.html$', 'pyv4.wiki.views.index'),
    (r'^downloads\.html$', 'pyv4.packages.views.index'),
    
    (r'^news-', include('pyv4.news.urls')),
    (r'^upload-', include('pyv4.upload.urls')),
    (r'^user-', include('pyv4.users.urls')),
    (r'^forum-', include('pyv4.forum.urls')),
    (r'^wiki-', include('pyv4.wiki.urls')),
    (r'^packages-', include('pyv4.packages.urls')),
    (r'^demand-', include('pyv4.demands.urls')),
    (r'^mp-', include('pyv4.mp.urls')),
    (r'^feeds/', include('pyv4.feeds.urls')),
    (r'^pastebin-', include('pyv4.pastebin.urls')),

    (r'^login\.html$', 'pyv4.general.views.login'),
    (r'^login-1\.html$', 'pyv4.general.views.login_validate'),
    (r'^logout-(?P<user_id>\d+)\.html$', 'pyv4.general.views.logout'),
    (r'^register\.html$', 'pyv4.general.views.register'),
    (r'^search-(?P<page>\d+)\.html$', 'pyv4.general.views.search'),
    (r'^captcha.png$', 'pyv4.general.captcha.captcha'),
    (r'^devcorner.html$', 'pyv4.general.views.devcorner'),
                       
    (r'^i18n/', include('django.conf.urls.i18n')),
    
    (r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STYLE_ROOT}),
    (r'^files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
                       
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
