import datetime
import logging
import pickle
import re
from typing import Union, Dict, Optional

import django_rq
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.utils.timezone import now
from dynamic_preferences.registries import global_preferences_registry
from federation.types import RequestType

from socialhome import __version__ as version
from socialhome.content.enums import ContentType
from socialhome.federate.models import Payload

logger = logging.getLogger("socialhome")


def get_matrix_config() -> Optional[Dict]:
    """
    Matrix configuration object for the federation library.
    """
    if settings.SOCIALHOME_MATRIX_ENABLED:
        return {
            "homeserver_base_url": settings.SOCIALHOME_MATRIX_APPSERVICE_BASE_URL,
            "homeserver_name": settings.SOCIALHOME_DOMAIN,
            "homeserver_domain_with_port": settings.SOCIALHOME_MATRIX_APPSERVICE_DOMAIN_WITH_PORT,
            "appservice": {
                "id": settings.SOCIALHOME_MATRIX_APPSERVICE_ID,
                "shortcode": settings.SOCIALHOME_MATRIX_APPSERVICE_SHORTCODE,
                "token": settings.SOCIALHOME_MATRIX_APPSERVICE_TOKEN,
            },
        }


def get_nodeinfo2_data():
    """
    Return data set for a NodeInfo2 document.
    """
    from socialhome.content.models import Content  # Circulars
    from socialhome.users.models import User  # Circulars
    site = Site.objects.get_current()
    data = {
        "server": {
            "baseUrl": settings.SOCIALHOME_URL,
            "name": site.name,
            "software": "socialhome",
            "version": version,
        },
        "relay": "none",
        "openRegistrations": settings.ACCOUNT_ALLOW_REGISTRATION,
    }
    if settings.SOCIALHOME_STATISTICS:
        data.update({"usage": {
            "users": {
                "total": User.objects.count(),
                "activeHalfyear": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=180)).count(),
                "activeMonth": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=30)).count(),
                "activeWeek": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=7)).count(),
            },
            "localPosts": Content.objects.filter(author__user__isnull=False, content_type=ContentType.CONTENT).count(),
            "localComments": Content.objects.filter(author__user__isnull=False, content_type=ContentType.REPLY).count(),
        }})
    if settings.SOCIALHOME_SHOW_ADMINS:
        data.update({"organization": {
            "contact": settings.ADMINS[0][1],
            "name": settings.ADMINS[0][0],
        }})
    return data


def get_outbound_payload_logger() -> Optional[callable]:
    """
    Return a function to log outbound payloads, if enabled in admin preferences.
    """
    preferences = global_preferences_registry.manager()
    if preferences["admin__log_all_outbound_payloads"]:
        return outbound_payload_logger


def outbound_payload_logger(payload: Union[str, Dict], protocol: str, sender: str) -> None:
    """
    Log an outbound payload.
    """
    Payload.objects.create(
        body=str(payload),
        direction="outbound",
        entities_found=1,
        headers="",
        method="",
        protocol=protocol,
        sender=sender,
        url="",
    )


def queue_payload(request: HttpRequest, uuid: str = None):
    """
    Queue payload for processing.
    """
    from socialhome.federate.tasks import receive_task  # Circulars
    try:
        # Create a simpler request object we can push to RQ
        headers = {}
        for key, value in request.META.items():
            key = key.replace('HTTP_', '').lower().replace('_', '-').capitalize()
            try:
                pickle.dumps(value)
            except Exception:
                pass
            else:
                headers[key] = value
                # Include also a lowercase version for compatibility with signature verification module
                headers[key.lower()] = value
        _request = RequestType(
            body=request.body,
            headers=headers,
            method=request.method,
            url=request.build_absolute_uri(),
        )
        preferences = global_preferences_registry.manager()
        if preferences["admin__log_all_receive_payloads"]:
            logger.debug("queue_payload - Request: %s", _request)

        if not uuid:
            # Check if profile path has an uuid
            match = re.match(r"^/p/([0-9a-z-]+)/inbox/$", request.path)
            if match:
                uuid = match.groups()[0]

        queue = django_rq.get_queue("high")
        queue.enqueue(receive_task, _request, uuid=uuid)
        return True
    except Exception:
        logger.exception('Failed to enqueue payload')
        return False
