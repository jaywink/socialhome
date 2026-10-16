from asgiref.sync import iscoroutinefunction
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render
from django.utils.decorators import sync_and_async_middleware

from socialhome.users.models import User

@sync_and_async_middleware
def AdminApprovalMiddleware(get_response):
    if iscoroutinefunction(get_response):
        async def middleware(request):
            response = None
            admin_approved = None
            # If we require admin approvals, and the user is not approved, render a waiting page.
            # Always allow the auth flows, however.
            if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
                if  request.path.startswith('/api/allauth/browser/v1/auth/session') \
                    or request.path.startswith('/api/allauth/browser/v1/auth/login') \
                    or request.path.startswith('/api/allauth/browser/v1/auth/signup') \
                    or request.path.startswith('/api/allauth/browser/v1/auth/email/verify'):
                    response = await get_response(request)
                    if response.status_code != 200: return response
                    try:
                        content = json.loads(response.content)
                        user_id = content['data']['user']['id']
                        user = await User.objects.aget(id=user_id)
                        admin_approved = getattr(user, 'admin_approved', None)
                    except KeyError:
                        user = None
                if getattr(await request.auser(), "admin_approved", admin_approved) is False and \
                    not (request.path.startswith('/accounts') \
                        or request.path.startswith('/admin')):
                    if request.path.startswith('/api'):
                        if not response:
                            request.user = AnonymousUser()
                            response = await get_response(request)
                            if response.status_code == 200: return response
                        response.status_code = 401
                        response.content  = json.dumps({'status': 401,
                                                       "data": {
                                                           "flows":[
                                                               {
                                                                   "id": "admin_approval_required",
                                                                   "is_pending": True
                                                               }
                                                           ]
                                                       },
                                                       "meta": {
                                                           "is_authenticated": False
                                                       }
                                                       })
                        response.content_type = "application/json"
                        return response
                    else:
                        return render(request, 'users/admin_approval_required.html')
                else: return response if response else await get_response(request)

            else: return await get_response(request)
    else:
        def middleware(request):
            response = None
            admin_approved = None
            # If we require admin approvals, and the user is not approved, render a waiting page.
            # Always allow the auth flows, however.
            if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
                if  request.path.startswith('/api/allauth/browser/v1/auth/session') \
                    or request.path.startswith('/api/allauth/browser/v1/auth/login') \
                    or request.path.startswith('/api/allauth/browser/v1/auth/signup') \
                    or request.path.startswith('/api/allauth/browser/v1/auth/email/verify'):
                    response = get_response(request)
                    if response.status_code != 200: return response
                    try:
                        content = json.loads(response.content)
                        user_id = content['data']['user']['id']
                        user = User.objects.get(id=user_id)
                        admin_approved = getattr(user, 'admin_approved', None)
                    except KeyError:
                        user = None
                if getattr(request.user, 'admin_approved', admin_approved) is False and \
                    not (request.path.startswith('/accounts') \
                        or request.path.startswith('/admin')):
                    if request.path.startswith('/api'):
                        if not response:
                            request.user = AnonymousUser()
                            response = get_response(request)
                            if response.status_code == 200: return response
                        response.status_code = 401
                        response.content  = json.dumps({'status': 401,
                                                       "data": {
                                                           "flows":[
                                                               {
                                                                   "id": "admin_approval_required",
                                                                   "is_pending": True
                                                               }
                                                           ]
                                                       },
                                                       "meta": {
                                                           "is_authenticated": False
                                                       }
                                                       })
                        response.content_type = "application/json"
                        return response
                    else:
                        return render(request, 'users/admin_approval_required.html')
                else: return response if response else get_response(request)

            else: return get_response(request)

    return middleware
