# -*- coding: utf-8 -*-
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return getattr(settings, 'ACCOUNT_ALLOW_REGISTRATION', True)

    def new_user(self, request):
        user = super().new_user(request)
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
            user.admin_approved = False
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return getattr(settings, 'ACCOUNT_ALLOW_REGISTRATION', True)

    def new_user(self, request, sociallogin):
        user = super().new_user(request, sociallogin)
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
            user.admin_approved = False
        return user
