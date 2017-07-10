from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from django.views.i18n import javascript_catalog
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from socialhome.views import HomeView
from socialhome.users.viewsets import UserViewSet, ProfileViewSet

js_translations = {
    "packages": ("socialhome",),
}

# API routes
router = DefaultRouter()
router.register(r"profiles", ProfileViewSet)
router.register(r"users", UserViewSet)

urlpatterns = [
    url(r"", include("socialhome.federate.urls", namespace="federate")),

    # Streams
    url(r"", include("socialhome.streams.urls", namespace="streams")),

    url(r"^$", HomeView.as_view(), name="home"),
    url(r"^about/$", TemplateView.as_view(template_name="pages/about.html"), name="about"),

    # User management
    url(r"", include("socialhome.users.urls", namespace="users")),
    url(r"^accounts/", include("allauth.urls")),

    # Markdownx
    url(r"^markdownx/", include("markdownx.urls")),

    # Content
    url(r"^content/", include("socialhome.content.urls", namespace="content")),

    # JavaScript translations
    url(r"^jsi18n/$", javascript_catalog, js_translations, name="javascript-catalog"),

    # Admin pages
    url(settings.ADMIN_URL, include(admin.site.urls)),
    url(r"^django-rq/", include("django_rq.urls")),

    # API
    url(r"^api/", include(router.urls, namespace="api")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api-token-auth/", obtain_auth_token),

    # Preferences
    url(r"^preferences/", include("dynamic_preferences.urls")),

    # Search
    url(r"^search/", include("socialhome.search.urls", namespace="search")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r"^400/$", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}),
        url(r"^403/$", default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")}),
        url(r"^404/$", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}),
        url(r"^500/$", default_views.server_error),
    ]
    if settings.DEBUG_TOOLBAR_ENABLED:
        import debug_toolbar
        urlpatterns += [
            url(r"^__debug__/", include(debug_toolbar.urls)),
        ]

if settings.MOCHA_TESTS:
    urlpatterns += [
        url(r"mocha/", include("mocha.urls")),
    ]
