from django.conf import settings
from django.shortcuts import redirect, render


class AdminApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If we require admin approvals, and the user is not approved, render a waiting page.
        # Always allow the auth flows, however.
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL and getattr(request.user, "admin_approved", None) is False and \
                not request.path.startswith('/accounts'):
            return render(request, 'users/admin_approval_required.html')

        return self.get_response(request)


def use_new_ui(get_response):
    def middleware(request):
        use_new_ui = True
        if request.user.is_authenticated:
            use_new_ui = request.user.preferences['generic__use_new_ui']
        if use_new_ui and request.method in ('GET', 'HEAD'):
            ap_request = False
            accept = request.META.get('HTTP_ACCEPT', '')
            for content_type in (
                'application/activity+json',
                'application/ld+json',
                #'application/xml',
                'application/magic-envelope+xml',
                'application/xrd+xml',
            ):
                if accept.find(content_type) > -1:
                    ap_request = True
                    break
            if not any((
                request.path.split('/')[1] in (
                    '.well-known',
                    'accounts',
                    'admin',
                    'api',
                    'ch',
                    'django-rq',
                    'fetch',
                    'hcard',
                    'jsi18n',
                    'nodeinfo',
                    'static',
                    'webfinger',
                ),
                request.path.endswith('.xml'),
                ap_request,
            )):
                return render(request, 'index.html')

        return get_response(request)

    return middleware
