from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views import defaults as default_views
from django.views.i18n import JavaScriptCatalog
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from django_js_reverse.views import urls_js
from dynamic_preferences.users.viewsets import UserPreferencesViewSet

from socialhome.content.views import ContentCreateView
from socialhome.content.viewsets import ContentViewSet, TagViewSet
from socialhome.enums import PolicyDocumentType
from socialhome.search.viewsets import SearchViewSet
from socialhome.viewsets import ImageUploadView, MediaUploadView, settings_view
from socialhome.views import (
    HomeView, MarkdownXImageUploadView, ObtainSocialhomeAuthToken, PolicyDocumentView)
from socialhome.users.viewsets import UserViewSet, ProfileViewSet

router = DefaultRouter()
router.register(r"content", ContentViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"search", SearchViewSet, basename="search")
router.register(r"tags", TagViewSet)
router.register(r"users", UserViewSet)
router.register(r"preferences/user", UserPreferencesViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title=f"{settings.SOCIALHOME_DOMAIN} API",
      default_version='v1',
      terms_of_service=f"{settings.SOCIALHOME_URL}/terms/",
      contact=openapi.Contact(email=settings.SOCIALHOME_CONTACT_EMAIL),
      license=openapi.License(name="AGPLv3"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r"", include("socialhome.federate.urls", namespace="federate")),

    re_path(r'^robots\.txt', include('robots.urls')),

    # Streams
    re_path(r"^streams/", include("socialhome.streams.urls.views", namespace="streams")),

    re_path(r"^$", HomeView.as_view(), name="home"),

    # User management
    re_path(r"", include("socialhome.users.urls", namespace="users")),
    re_path(r"^accounts/", include("allauth.urls")),
    re_path(r"^api/allauth/", include("allauth.headless.urls")),

    # Markdownx
    # Use our own upload view based on the MarkdownX view
    re_path(r"^markdownx/upload/$", MarkdownXImageUploadView.as_view(), name="markdownx_upload"),
    re_path(r"^markdownx/", include("markdownx.urls")),

    # Content
    re_path(r"^content/", include("socialhome.content.urls", namespace="content")),
    # Fallback for bookmarklet route for cross-project support
    re_path(r"^bookmarklet/", ContentCreateView.as_view(), name="bookmarklet"),

    # JavaScript translations
    path("jsi18n/", JavaScriptCatalog.as_view(packages=['socialhome'], domain="django") , name="javascript-catalog"),

    # Admin pages
    re_path(settings.ADMIN_URL, admin.site.urls),
    re_path(r"^django-rq/", include("django_rq.urls")),

    # API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^api/swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r"^api/", include((router.urls, "api"))),
    re_path(r"^api/image-upload/$", ImageUploadView.as_view(), name="api-image-upload"),
    re_path(r"^api/media-upload/$", MediaUploadView.as_view(), name="api-media-upload"),
    re_path(r"^api/streams/", include("socialhome.streams.urls.api", namespace="api-streams")),
    re_path(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    re_path(r"^api-token-auth/", ObtainSocialhomeAuthToken.as_view(), name="api-token-auth"),
    re_path(r"^api/settings/", settings_view, name="settings"),

    # Account
    re_path(r"^account/", include("dynamic_preferences.urls")),

    # Search
    re_path(r"^search/", include("socialhome.search.urls", namespace="search")),

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
        re_path(r'^_silk/', include('silk.urls', namespace='silk')),
    ]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        re_path(r"^400/$", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}),
        re_path(r"^403/$", default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")}),
        re_path(r"^404/$", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}),
        re_path(r"^500/$", default_views.server_error),
    ]
    if settings.DEBUG_TOOLBAR_ENABLED:
        import debug_toolbar
        urlpatterns += [
            re_path(r"^__debug__/", include(debug_toolbar.urls)),
        ]

if settings.SOCIALHOME_ADDITIONAL_APPS_URLS:
    url_prefix, url_path = settings.SOCIALHOME_ADDITIONAL_APPS_URLS.split(',')
    urlpatterns += [
        re_path(url_prefix, include(url_path)),
    ]
