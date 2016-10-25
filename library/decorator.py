from django.http import HttpResponseRedirect

def login_required(func):
    def wrapper(request, *args, **kwrds):
        if request.user['is_authenticated']:
            return func(request, *args, **kwrds)
        else:
            return HttpResponseRedirect('/')
    return wrapper

