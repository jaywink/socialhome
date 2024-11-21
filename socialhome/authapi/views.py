from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import json

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
#from .forms import CreateUserForm

from socialhome.users.serializers import ProfileSerializer

@ensure_csrf_cookie
@require_http_methods(['GET'])
def set_csrf_token(request):
    """
    We set the CSRF cookie on the frontend.
    """
    return JsonResponse({'message': 'CSRF cookie set'})


@require_http_methods(['POST'])
def login_view(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data['username']
        password = data['password']
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON'}, status=400
        )

    user = authenticate(request, username=username, password=password)

    if user:
        login(request, user)
        data = ProfileSerializer(user.profile, context={"request": request}).data
        return JsonResponse(data)
    return JsonResponse(
        {'success': False, 'message': 'Invalid credentials'}, status=401
    )


def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out'})


#@require_http_methods(['GET'])
#def user(request):
#    if request.user.is_authenticated:
#        return JsonResponse(
#            {'username': request.user.username, 'email': request.user.email}
#        )
#    return JsonResponse(
#        {'message': 'Not logged in'}, status=401
#    )


#@require_http_methods(['POST'])
#def register(request):
#    data = json.loads(request.body.decode('utf-8'))
#    form = CreateUserForm(data)
#    if form.is_valid():
#        form.save()
#        return JsonResponse({'success': 'User registered successfully'}, status=201)
#    else:
#        errors = form.errors.as_json()
#        return JsonResponse({'error': errors}, status=400)

