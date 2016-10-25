from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('bingo.views',
    url(r'^create$', 'create_game', name='create_game'),
    url(r'^claim/(?P<game_id>[\w-]+)/(?P<claim_type>[\w-]+)', 'claim', name='claim'),
    url(r'^clicked-number/(?P<game_id>[\w-]+)/(?P<number>\d+)', 'clicked_number', name='clicked_number'),
    url(r'create-ticket/(?P<game_id>[\w-]+)', 'create_ticket', name='create_ticket'),
	url(r'^(?P<game_id>[\w-]+)', 'game', name='game'),
    url(r'', 'game_list', name='game_list'),
)