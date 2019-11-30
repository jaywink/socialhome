from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.i18n import JavaScriptCatalog
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from django_js_reverse.views import urls_js

from socialhome.content.views import ContentBookmarkletView
from socialhome.content.viewsets import ContentViewSet, TagViewSet
from socialhome.enums import PolicyDocumentType
from socialhome.viewsets import ImageUploadView
from socialhome.views import (
    HomeView, MarkdownXImageUploadView, ObtainSocialhomeAuthToken, PolicyDocumentView)
from socialhome.users.viewsets import UserViewSet, ProfileViewSet

# API routes
# NOTE! If changing or adding API urls, don't forget to update the JS tests URL config fixtures as follows:
#
#    python manage.py collectstatic_js_reverse
#    mv staticfiles/django_js_reverse/js/reverse.js socialhome/frontend/tests/unit/fixtures/Urls.js
#    rm -rf staticfiles/django_js_reverse
#
router = DefaultRouter()
router.register(r"content", ContentViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"tags", TagViewSet)
router.register(r"users", UserViewSet)

# API docs
schema_view = get_schema_view(title="Socialhome API")

urlpatterns = [
    url(r"", include("socialhome.federate.urls", namespace="federate")),

    url(r'^robots\.txt', include('robots.urls')),

    # Streams
    url(r"^streams/", include("socialhome.streams.urls.views", namespace="streams")),

    url(r"^$", HomeView.as_view(), name="home"),

    # User management
    url(r"", include("socialhome.users.urls", namespace="users")),
    url(r"^accounts/", include("allauth.urls")),

    # Markdownx
    # Use our own upload view based on the MarkdownX view
    url(r"^markdownx/upload/$", MarkdownXImageUploadView.as_view(), name="markdownx_upload"),
    url(r"^markdownx/", include("markdownx.urls")),

    # Content
    url(r"^content/", include("socialhome.content.urls", namespace="content")),
    # Fallback for bookmarklet route for cross-project support
    url(r"^bookmarklet/", ContentBookmarkletView.as_view(), name="bookmarklet"),

    # JavaScript translations
    path("jsi18n/", JavaScriptCatalog.as_view(packages=['socialhome']), name="javascript-catalog"),

    # Django URLs in JS
    url(r"^jsreverse/$", urls_js, name="js_reverse"),

    # Admin pages
    url(settings.ADMIN_URL, admin.site.urls),
    url(r"^django-rq/", include("django_rq.urls")),

    # API
    url(r"^api/$", schema_view, name="api-docs"),
    url(r"^api/", include((router.urls, "api"))),
    url(r"^api/image-upload/$", ImageUploadView.as_view(), name="api-image-upload"),
    url(r"^api/streams/", include("socialhome.streams.urls.api", namespace="api-streams")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api-token-auth/", ObtainSocialhomeAuthToken.as_view(), name="api-token-auth"),

    # Account
    url(r"^account/", include("dynamic_preferences.urls")),

    # Search
    url(r"^search/", include("socialhome.search.urls", namespace="search")),

    # Policy docs
    path(
        'privacy/',
        PolicyDocumentView.as_view(),
        {'document_type': PolicyDocumentType.PRIVACY_POLICY},
        name="privacy-policy"
    ),
    path(
        'terms/',
        PolicyDocumentView.as_view(),
        {'document_type': PolicyDocumentType.TERMS_OF_SERVICE},
        name="terms-of-service"
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SILKY_INSTALLED:
    urlpatterns += [
        url(r'^_silk/', include('silk.urls', namespace='silk')),
    ]

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

if settings.SOCIALHOME_ADDITIONAL_APPS_URLS:
    url_prefix, url_path = settings.SOCIALHOME_ADDITIONAL_APPS_URLS.split(',')
    urlpatterns += [
        url(url_prefix, include(url_path)),
    ]
