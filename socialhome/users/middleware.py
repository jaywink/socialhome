from django.conf import settings
from django.shortcuts import render


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
