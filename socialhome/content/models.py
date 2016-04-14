# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.utils.text import truncate_letters
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

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
