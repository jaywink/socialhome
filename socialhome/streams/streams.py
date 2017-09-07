from socialhome.content.models import Content


class BaseStream:
    last_id = None
    ordering = "-created"
    paginate_by = 15

    def __init__(self, last_id=None, user=None, **kwargs):
        self.last_id = last_id
        self.user = user

    def get_content(self):
        """Get queryset of Content objects."""
        return Content.objects.filter(id__in=self.get_content_ids()).prefetch_related("tags").order_by(self.ordering)

    def get_content_ids(self):
        """Get a list of content ID's."""
        qs = self.get_queryset()
        if self.last_id:
            if self.ordering == "-created":
                qs = qs.filter(id__lt=self.last_id)
            else:
                qs = qs.filter(id__gt=self.last_id)
        return qs.values_list("id", flat=True).order_by(self.ordering)[:self.paginate_by]

    def get_queryset(self):
        raise NotImplemented


class FollowedStream(BaseStream):
    def get_queryset(self):
        return Content.objects.followed(self.user)


class PublicStream(BaseStream):
    def get_queryset(self):
        return Content.objects.public()


class TagStream(BaseStream):
    def __init__(self, tag, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag

    def get_queryset(self):
        if not self.tag:
            raise AttributeError("TagStream is missing tag.")
        return Content.objects.tag(self.tag, self.user)
