import coreapi
import coreschema

from django.utils.decorators import method_decorator
from django.views import View
from federation.entities.activitypub.django.views import activitypub_object_view
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.views import APIView

from socialhome.users.serializers import LimitedProfileSerializer


@method_decorator(activitypub_object_view, name='get')
class HomeView(View):
    def get(self, request, *args, **kwargs):
        return super(HomeView, self).get(request, *args, **kwargs)


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
