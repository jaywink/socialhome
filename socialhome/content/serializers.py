import operator
import re
from functools import reduce
from typing import Dict, Any, Set, List
import traceback

from django.db.models import Q
from django.utils.translation import ngettext as _
from enumfields.drf import EnumField
from federation.utils.text import validate_handle
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField, BooleanField

from socialhome.content.enums import ContentType
from socialhome.content.models import Content, Tag
from socialhome.content.signals import render_content
from socialhome.content.utils import safe_text_for_markdown, update_counts
from socialhome.enums import Visibility
from socialhome.users.models import Profile
from socialhome.users.serializers import LimitedProfileSerializer


class RecipientsField(serializers.Field):
    def get_value(self, dictionary: Dict[str, Any]) -> Set[str]:
        raw_recipients = set()
        for r in dictionary.get("recipients", ""):
            r2 = r.strip()
            if len(r2) > 0:
                raw_recipients.add(r2)

        return raw_recipients

    def get_attribute(self, instance: Content) -> Set[str]:
        """
        Add the mentions for public content or
        add the previous values from limited visibilities for existing limited content.
        TODO: fix finger case sensitivity potentially causing both handle and finger to
        return a recipient
        """
        if instance.visibility == Visibility.LIMITED:
            fingers = instance.limited_visibilities.filter(finger__isnull=False).order_by("id").values_list("finger", flat=True)
            # Legacy?
            handles = instance.limited_visibilities.filter(fid__isnull=True).order_by("id").values_list("handle", flat=True)
            fids = instance.limited_visibilities.filter(handle__isnull=True).order_by("id").values_list("fid", flat=True)
            both = instance.limited_visibilities.filter(
                handle__isnull=False, fid__isnull=False,
            ).order_by("id").values_list("handle", flat=True)
            return set(list(handles) + list(fids) + list(both) + list(fingers))
        else:
            return set(instance.mentions.all().values_list("finger", flat=True))

    def to_internal_value(self, data: Set[str]) -> Set[str]:
        return data

    def to_representation(self, value: Set[str]) -> List[str]:
        return list(value)


class ContentSerializer(serializers.ModelSerializer):
    author = LimitedProfileSerializer(read_only=True)
    content_type = EnumField(ContentType, ints_as_names=True, read_only=True)
    include_following = BooleanField(default=False)
    notify_key = SerializerMethodField()
    recipients = RecipientsField()
    user_is_author = SerializerMethodField()
    user_has_shared = SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    through = SerializerMethodField()
    through_author = SerializerMethodField()
    visibility = EnumField(Visibility, lenient=True, ints_as_names=True, required=False)

    class Meta:
        model = Content
        fields = (
            "author",
            "content_type",
            "edited",
            "federate",
            "uuid",
            "has_twitter_oembed",
            "humanized_timestamp",
            "id",
            "is_nsfw",
            "include_following",
            "local",
            "notify_key",
            "order",
            "parent",
            "pinned",
            "recipients",
            "remote_created",
            "rendered",
            "reply_count",
            "root_parent",
            "service_label",
            "share_of",
            "shares_count",
            "show_preview",
            "slug",
            "tags",
            "text",
            "through",
            "through_author",
            "timestamp",
            "timestamp_epoch",
            "url",
            "user_is_author",
            "user_has_shared",
            "visibility",
        )
        read_only_fields = (
            "author",
            "content_type",
            "edited",
            "uuid",
            "has_twitter_oembed",
            "humanized_timestamp",
            "id",
            "is_nsfw",
            "local",
            "notify_key",
            "remote_created",
            "rendered",
            "reply_count",
            "root_parent",
            "share_of",
            "shares_count",
            "slug",
            "tags",
            "through",
            "through_author",
            "timestamp",
            "timestamp_epoch",
            "url",
            "user_is_author",
            "user_has_shared",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_through_authors()

    def get_author_uuid(self, obj):
        return obj.author.uuid

    def get_notify_key(self, obj):
        return "streams_content__%s" % obj.channel_group_name

    def cache_through_authors(self):
        """
        If we have 'throughs', cache author information here for all of them.
        """
        request = self.context.get("request")
        if not self.context.get("throughs") or not request:
            self.context["throughs_authors"] = {}
            return
        throughs_ids = self.context["throughs"]
        ids = {value for _key, value in throughs_ids.items()}
        through_to_id = {value: key for key, value in throughs_ids.items()}
        throughs = Content.objects.visible_for_user(request.user).select_related("author").filter(id__in=list(ids))
        self.context["throughs_authors"] = {through_to_id.get(c.id, c.id): c.author for c in throughs}

    def get_through(self, obj):
        """
        Through is generally required only for serializing content for streams.
        Since through is now a model field instead of an annotation, it's expected
        to have a sane value (one of id or latest share id). This method  is kept
        so that contents predating the addition of the through field are properly
        updated.
        """
        if obj.through == 0:
            obj.through = obj.shares.values_list('id', flat=True).last() or obj.id
            Content.objects.filter(id=obj.id).update(through=obj.through)
        return obj.through

    def get_through_author(self, obj):
        throughs_authors = self.context.get("throughs_authors")
        if not throughs_authors:
            try:
                through_author = Content.objects.get(id=self.get_through(obj)).author
            except Content.DoesNotExist:
                through_author = obj.author
        else:
            through_author = throughs_authors.get(obj.id, obj.author)
        if through_author != obj.author:
            return LimitedProfileSerializer(
                instance=through_author,
                read_only=True,
                context={"request": self.context.get("request")},
            ).data
        return {}

    def get_user_is_author(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return bool(request.user.is_authenticated and obj.author == request.user.profile)

    def get_user_has_shared(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return Content.has_shared(obj.id, request.user.profile.id) if hasattr(request.user, "profile") else False

    def validate_parent(self, value):
        # Validate parent cannot be changed
        if self.instance and value != self.instance.parent:
            raise serializers.ValidationError("Parent cannot be changed for an existing Content instance.")
        # Validate user can see parent
        if not self.instance and value:
            request = self.context.get("request")
            if not value.visible_for_user(request.user):
                raise serializers.ValidationError("Parent not found")

        return value

    def to_representation(self, instance: Content) -> Dict[str, Any]:
        update_counts(instance)
        result = dict(super().to_representation(instance))
        if not self.get_user_is_author(instance):
            result["recipients"] = ""

        return result

    def save(self, **kwargs: Dict):
        """
        Set possible recipients after save.
        """
        updating = self.instance is not None
        raw_recipients = self.validated_data.pop("recipients", "")
        parent = self.validated_data.get("parent")
        user = self.context.get("request").user

        # Get previous recipients, if old instance
        previous_recipients = []
        if updating:
            if not self.instance.author_id:
                self.instance.author = user.profile

            if self.instance.limited_visibilities.count():
                previous_recipients = self.instance.limited_visibilities.values_list("id", flat=True)

            if parent is not None:
                self.instance.parent = parent
                # HAXX to ensure visibility is empty when going in to save
                self.instance.visibility = None

        content = super().save(**kwargs)

        # Mentions now == recipients entered through the UI
        existing_handles = set(content.mentions.values_list('finger', flat=True))
        to_remove = existing_handles.difference(raw_recipients)
        to_add = raw_recipients.difference(existing_handles)
        for handle in to_remove:
            try:
                content.mentions.remove(Profile.objects.get(finger__iexact=handle))
            except Profile.DoesNotExist:
                pass
        for handle in to_add:
            try:
                content.mentions.add(Profile.objects.get(finger__iexact=handle))
            except Profile.DoesNotExist:
                pass
        # Linkify mentions
        render_content(content)

        if content.visibility != Visibility.LIMITED or content.content_type == ContentType.SHARE:
            return content

        if content.content_type == ContentType.CONTENT:
            # Collect new recipients
            # TODO: maybe filtering only on finger is enough now?
            recipients = Profile.objects.none()
            if raw_recipients:
                recipients = Profile.objects.filter(
                    Q(handle__in=raw_recipients) | \
                    reduce(operator.or_, (Q(finger__iexact=x) for x in raw_recipients)) | \
                    Q(fid__in=raw_recipients)
                ).visible_for_user(user)

            # Add mutuals, if included
            if self.validated_data.get("include_following"):
                mutuals = Profile.objects.filter(followers=user.profile).intersection(
                    Profile.objects.filter(following=user.profile))
                recipients = recipients.union(mutuals)
        elif content.content_type == ContentType.REPLY:
            # Should mentions be added as recipients here too?
            recipients = content.root_parent.limited_visibilities.all()
        else:
            return content

        # If old instance, first remove the now not present to trigger federation retraction
        if previous_recipients:
            to_remove = set(previous_recipients).difference(set(recipients.values_list("id", flat=True)))
            for remove_id in to_remove:
                profile = Profile.objects.get(id=remove_id)
                content.limited_visibilities.remove(profile)

        # Clear, then set, since federation will be triggered by m2m changed signal
        content.limited_visibilities.clear()
        content.limited_visibilities.set(recipients)

        return content

    def validate(self, data):
        """
        Validate visibility is not required for replies.

        If given, make sure it is the same as parent. If not given, use parent visibility.
        """
        parent = data.get("parent")
        if parent:
            if data.get("visibility") and parent.visibility != data.get("visibility"):
                raise serializers.ValidationError("Visibility was given but it doesn't match parent.")
            data["visibility"] = parent.visibility
        else:
            if not self.instance and not data.get("visibility"):
                raise serializers.ValidationError("Visibility is required")

        return data

    def validate_text(self, value):
        """Sanitize text if user is untrusted."""
        user = self.context.get("request").user
        if user.trusted_editor:
            return value
        return safe_text_for_markdown(value)

    def validate_recipients(self, value: Set[str]) -> Set[str]:
        if self.initial_data.get("visibility", Visibility.PUBLIC.value) != Visibility.LIMITED.value:
            return value

        if not value and not self.initial_data.get("include_following"):
            raise serializers.ValidationError("Recipients cannot be empty if not including followed users.")

        user = self.context.get("request").user

        validation_errors = []
        for recipient in value:
            if not validate_handle(recipient) and not re.match(r"https?://", recipient):
                validation_errors.append(recipient)

        if len(validation_errors) > 0:
            msg = _(
                "This recipient couldn't be found (please check the format).",
                "These recipients couldn't be found (please check the format).",
                len(validation_errors)
            )

            raise serializers.ValidationError({
                "code": "recipients_not_found_error",
                "message": msg,
                "payload": validation_errors,
            })

        recipient_profiles = Profile.objects.none()
        if value:
            recipient_profiles = Profile.objects.filter(
                Q(handle__in=value) | Q(fid__in=value) | \
                reduce(operator.or_, (Q(finger__iexact=x) for x in value))
                ).visible_for_user(user)

        # TODO we should probably try to lookup missing ones over the network first before failing
        if recipient_profiles.distinct().count() != len(set(value)):
            raise serializers.ValidationError("Not all recipients could be found.")

        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name", "created", "uuid")
        read_only_fields = ("created", "uuid")
