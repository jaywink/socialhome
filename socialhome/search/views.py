import xml

from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from federation.entities import base
from federation.fetchers import retrieve_remote_profile, retrieve_remote_content
from federation.utils.text import validate_handle
from haystack.generic_views import SearchView
from xapian import QueryParserError

from socialhome.content.models import Tag, Content
from socialhome.content.utils import safe_text
from socialhome.enums import Visibility
from socialhome.federate.utils import process_entities
from socialhome.search.utils import get_single_object
from socialhome.users.models import Profile
from socialhome.utils import is_url


class GlobalSearchView(SearchView):
    def get_context_data(self, *args, **kwargs):
        """Add tags results to the context."""
        context = super().get_context_data(*args, **kwargs)
        tags = self.get_tags_qs()
        tags_context = {
            'paginator': None,
            'page_obj': None,
            'is_paginated': False,
            'object_list': tags,
        }
        page_size = self.get_paginate_by(tags)
        if page_size:
            try:
                paginator, page, queryset, is_paginated = self.paginate_queryset(tags, page_size)
            except Http404:
                pass
            else:
                tags_context = {
                    'paginator': paginator,
                    'page_obj': page,
                    'is_paginated': is_paginated,
                    'object_list': queryset,
                }
        context['tags'] = tags_context
        return context

    def get_queryset(self):
        """Exclude some information from the queryset.

        If logged in, exclude own profile and SELF+LIMITED profiles
        If not logged in, exclude all but PUBLIC profiles

        We exclude SELF profiles too, though they should never even be indexed.
        """
        queryset = super().get_queryset()
        return self.filter_queryset(queryset)

    def get_tags_qs(self):
        """
        Retrieve tags.
        """
        return Tag.objects.annotate(
            content_count=Count('contents')
        ).filter(
            content_count__gt=0,
            name__icontains=self.q,
        ).order_by('name')

    def get(self, request, *args, **kwargs):
        """See if we have a direct match. If so redirect, if not, search.

        Try fetching a remote profile if the search term is a handle or fid.
        """
        q = safe_text(request.GET.get("q"))
        if q:
            q = q.strip().strip("@")
        self.q = q
        # Check if direct tag matches
        resp = get_single_object(q, request, *args, **kwargs)
        if not resp:
            try:
                return super().get(request, *args, **kwargs)
            except QueryParserError:
                # Re-render the form
                messages.warning(self.request, _("Search string is invalid, please try another one."))
                return HttpResponseRedirect(self.get_success_url())
        else: return resp

    def filter_queryset(self, queryset):
        """Do some of our own filtering on the queryset before returning."""
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(id=self.request.user.profile.id)
            if self.request.user.is_staff:
                return queryset
            else:
                # TODO: LIMITED profiles are excluded from searches even though the user might already be following
                # one of them. This is an unfortunate issue that should be tackled at some point, to allow searching for
                # LIMITED profiles that the user has a follow relationship with.
                return queryset.exclude(profile_visibility__in=[
                    Visibility.SELF.value, Visibility.LIMITED.value
                ])
        return queryset.exclude(profile_visibility__in=[
            Visibility.LIMITED.value, Visibility.SITE.value, Visibility.SELF.value
        ])
