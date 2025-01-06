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
        if request.user.is_authenticated:
            if request.user.preferences['generic__use_new_ui']:
                ap_request = False
                accept = request.META.get('HTTP_ACCEPT', '')
                for content_type in (
                    'application/activity+json', 'application/ld+json',
                ):
                    if accept.find(content_type) > -1:
                        ap_request = True
                        break
                if not any((
                    request.path.split('/')[1] in ('api', 'admin', 'ch', 'static'),
                    ap_request,
                )):
                    return render(request, 'index.html')

        return get_response(request)

    return middleware
