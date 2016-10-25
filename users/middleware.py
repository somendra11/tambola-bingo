import cass
from django.http import HttpResponse
from tweets.views import timeline

from library.decorator import login_required

def get_user(request):
    if 'username' in request.session:
        try:
            user = cass.get_user_by_username(request.session['username'])
            return {
                'username': user.username,
                'password': user.password,
                'is_authenticated': True
            }
        except cass.DatabaseError:
            pass
    return {
        'password': None,
        'is_authenticated': False,
    }

class LazyUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            request._cached_user = get_user(request)
        return request._cached_user

class UserMiddleware(object):

    def process_request(self, request):
        request.__class__.user = LazyUser()
        # return HttpResponse("process_request")

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass
        # return HttpResponse("process_view")

    # def process_view(self, request, view_func, view_args, view_kwargs):
    #    if view_func != timeline:
    #        call_it = login_required(view_func)
    #        result = call_it(request, *view_args, **view_kwargs)
    #        return result
    #    else:
    #        result = view_func(request, *view_args, **view_kwargs)
    #        return result

    # def process_template_response(self, request, response):
    #     return HttpResponse("response")

    # def process_response(self, request, response):
        # pass
        # return HttpResponse("response")
