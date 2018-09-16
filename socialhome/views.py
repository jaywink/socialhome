import coreapi
import coreschema
from importlib import import_module

from braces.views import LoginRequiredMixin
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.views.generic import TemplateView
from markdownx.utils import markdownify
from markdownx.views import ImageUploadView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.views import APIView

from socialhome.forms import MarkdownXImageForm
from socialhome.models import PolicyDocument
from socialhome.streams.views import FollowedStreamView, PublicStreamView
from socialhome.users.models import Profile
from socialhome.users.serializers import LimitedProfileSerializer
from socialhome.users.views import ProfileDetailView, ProfileAllContentView


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect to user detail view if root page is a profile or if the user is logged in"""

        if settings.SOCIALHOME_HOME_VIEW:
            p, m = settings.SOCIALHOME_HOME_VIEW.rsplit('.', 1)
            return getattr(import_module(p), m).as_view()(request)

        if request.user.is_authenticated:
            landing_page = request.user.preferences.get("generic__landing_page")
            if landing_page == "profile":
                return ProfileDetailView.as_view()(request, uuid=request.user.profile.uuid)
            elif landing_page == "profile_all":
                return ProfileAllContentView.as_view()(request, uuid=request.user.profile.uuid)
            elif landing_page == "followed":
                return FollowedStreamView.as_view()(request)
            elif landing_page == "public":
                return PublicStreamView.as_view()(request)
            else:
                # Fallback to profile view
                return ProfileDetailView.as_view()(request, uuid=request.user.profile.uuid)
        if settings.SOCIALHOME_ROOT_PROFILE:
            profile = get_object_or_404(Profile, user__username=settings.SOCIALHOME_ROOT_PROFILE)
            return ProfileDetailView.as_view()(request, uuid=profile.uuid)
        return super(HomeView, self).get(request, *args, **kwargs)


class MarkdownXImageUploadView(LoginRequiredMixin, ImageUploadView):
    form_class = MarkdownXImageForm
    raise_exception = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs


class ObtainSocialhomeAuthToken(ObtainAuthToken, APIView):
    # Documenting the API
    schema = AutoSchema(manual_fields=[
        coreapi.Field("username", description="User's username", required=True, location="form",
                      schema=coreschema.String()),
        coreapi.Field("password", description="User's password", required=True, location="form",
                      schema=coreschema.String()),
    ])

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        data = LimitedProfileSerializer(user.profile, context={"request": self.request}).data
        data.update({"token": token.key})
        return Response(data)


class PolicyDocumentView(TemplateView):
    template_name = "socialhome/policy_document.html"

    def dispatch(self, request, document_type=None, *args, **kwargs):
        if not document_type:
            return Http404()
        self.document = get_object_or_404(PolicyDocument, type=document_type.value, published_version__isnull=False)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = Template(self.document.published_content)
        template_context = Context({
            'domain': settings.SOCIALHOME_DOMAIN,
            'email': settings.SOCIALHOME_CONTACT_EMAIL,
            'maintainer': settings.SOCIALHOME_MAINTAINER,
            'jurisdiction': settings.SOCIALHOME_TOS_JURISDICTION,
        })
        rendered = template.render(template_context)
        context.update({
            'policy_title': self.document.type.label,
            'policy_content': markdownify(rendered),
            'policy_version': self.document.published_version,
        })
        return context
