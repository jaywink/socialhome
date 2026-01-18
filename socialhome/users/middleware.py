import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from socialhome.users.models import User

class AdminApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = None
        admin_approved = None
        # If we require admin approvals, and the user is not approved, render a waiting page.
        # Always allow the auth flows, however.
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
            if  request.path.startswith('/api/allauth/browser/v1/auth/session') \
                or request.path.startswith('/api/allauth/browser/v1/auth/login') \
                or request.path.startswith('/api/allauth/browser/v1/auth/signup') \
                or request.path.startswith('/api/allauth/browser/v1/auth/email/verify'):
                response = self.get_response(request)
                if response.status_code != 200: return response
                try:
                    content = json.loads(response.content)
                    user_id = content['data']['user']['id']
                    user = User.objects.get(id=user_id)
                    admin_approved = getattr(user, 'admin_approved', None)
                except KeyError:
                    user = None
            if getattr(request.user, "admin_approved", admin_approved) is False and \
                not (request.path.startswith('/accounts') \
                    or request.path.startswith('/admin')):
                if request.path.startswith('/api'):
                    if not response:
                        request.user = AnonymousUser()
                        response = self.get_response(request)
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
            else: return response if response else self.get_response(request)

        else: return self.get_response(request)
