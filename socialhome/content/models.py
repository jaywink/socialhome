# -*- coding: utf-8 -*-
from uuid import uuid4

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.utils.text import truncate_letters
from enumfields import EnumIntegerField
from markdownx.utils import markdownify
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from socialhome.content.enums import ContentTarget
from socialhome.enums import Visibility
from socialhome.users.models import User


class Post(models.Model):
    text = models.TextField(_("Text"), blank=True)
    # It would be nice to use UUIDField but in practise this could be anything due to other server implementations
    # and PostgreSQL is very picky with UUIDField.
    guid = models.CharField(_("GUID"), max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    public = models.BooleanField(_("Public"), default=True)
    remote_created = models.DateTimeField(_("Remote created"), blank=True, null=True)
    # For example mobile, server or application name
    service_label = models.CharField(_("Service label"), blank=True, max_length=32)
    created = AutoCreatedField(_('Created'), db_index=True)
    modified = AutoLastModifiedField(_('Modified'))

    def __str__(self):
        return "{text} ({guid})".format(
            text=truncate_letters(self.text, 100), guid=self.guid
        )

    def save(self, user=None, *args, **kwargs):
        if not self.pk and user:
            self.guid = uuid4()
            self.user = user
        return super(Post, self).save(*args, **kwargs)

    def render(self):
        return markdownify(self.text)


class Content(models.Model):
    """Model representing a piece of content.

    Actual content is linked by a GenericForeignKey. User and visibility is cached here for faster access.
    """
    target = EnumIntegerField(ContentTarget, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Content owner"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    visibility = EnumIntegerField(Visibility, default=Visibility.PUBLIC, db_index=True)

    def __str__(self):
        return "%s (%s, %s, %s)" % (
            self.content_type, self.object_id, self.target, self.visibility
        )
