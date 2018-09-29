from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    url('^auth/', include('users.urls')),
    # url('^one/', include('one.urls')),
    url('^game/', include('bingo.urls')),
    url('', include('tweets.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        (r'^media/(?P<path>.*)$', 'serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
