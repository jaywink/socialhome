# -*- coding: utf-8 -*-
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django_extensions.utils.text import truncate_letters
from enumfields import EnumIntegerField
from markdownx.utils import markdownify
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from socialhome.enums import Visibility
from socialhome.users.models import User, Profile


class Content(models.Model):
    text = models.TextField(_("Text"), blank=True)
    # It would be nice to use UUIDField but in practise this could be anything due to other server implementations
    guid = models.CharField(_("GUID"), max_length=255, unique=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name=_("Author"))
    visibility = EnumIntegerField(Visibility, default=Visibility.PUBLIC, db_index=True)

    # Is this content pinned to the user profile
    pinned = models.BooleanField(_("Pinned to profile"), default=False, db_index=True)
    # Order int to allow ordering content within some context, for example profile
    order = models.PositiveIntegerField(verbose_name=_("Order"), default=1, db_index=True)

    # For example mobile, server or application name
    service_label = models.CharField(_("Service label"), blank=True, max_length=32)
    remote_created = models.DateTimeField(_("Remote created"), blank=True, null=True)
    created = AutoCreatedField(_('Created'), db_index=True)
    modified = AutoLastModifiedField(_('Modified'))

    def __str__(self):
        return "{text} ({guid})".format(
            text=truncate_letters(self.text, 100), guid=self.guid
        )

    def save(self, author=None, *args, **kwargs):
        if not self.pk and author:
            self.guid = uuid4()
            self.author = author
        return super(Content, self).save(*args, **kwargs)

    def render(self):
        return markdownify(self.text)

    # TODO: make cached_property
    @property
    def rendered(self):
        return self.render()

    @staticmethod
    def get_contents_for_user(ids, user):
        contents = Content.objects.filter(id__in=ids)
        if not user.is_authenticated():
            contents = contents.filter(visibility=Visibility.PUBLIC)
        else:
            contents = contents.filter(
                Q(author=user.profile) | Q(visibility__in=[Visibility.SITE, Visibility.PUBLIC])
            )
        return contents.order_by("created")

    @staticmethod
    def get_rendered_contents_for_user(ids, user):
        contents = Content.get_contents_for_user(ids, user)
        rendered = []
        for content in contents:
            rendered.append({
                "id": content.id,
                "author": content.author_id,
                "rendered": content.rendered
            })
        return rendered
