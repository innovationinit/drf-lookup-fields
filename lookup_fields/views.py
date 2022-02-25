"""View mixins with customizable lookup field."""

from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
)

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ParseError
from rest_framework.generics import (
    GenericAPIView,
    get_object_or_404,
)

from .permissions import WithPermissions


class CustomizableLookupFieldMixin(object):

    """A mixin for API views with customizable lookup field specified in the request header Lookup-Field option"""

    DEFAULT_LOOKUP_FIELD: str = GenericAPIView.lookup_field
    HEADER_LOOKUP_FIELD_NAME: str = 'HTTP_LOOKUP_FIELD'  # matches the Lookup-Field header
    LOOKUP_FIELD_MAPPERS: Dict[str, List[Callable]] = {}
    LOOKUP_FIELD_VALIDATORS: Dict[str, List[Callable]] = {}  # Dict of lists of validators for each lookup field - field name as key
    lookup_url_kwarg = 'identifier'

    @property
    def ALLOWED_LOOKUP_FIELDS(self) -> List[str]:
        return [self.DEFAULT_LOOKUP_FIELD]

    @property
    def lookup_field(self) -> str:
        try:
            lookup_field = self.request.META[self.HEADER_LOOKUP_FIELD_NAME]
        except KeyError:
            lookup_field = self.DEFAULT_LOOKUP_FIELD

        permitted_lookup_fields = list(self._get_permitted_lookup_fields())

        if lookup_field not in permitted_lookup_fields:
            raise ParseError(_('Only {allowed_fields} lookup fields are allowed.').format(
                allowed_fields=', '.join(permitted_lookup_fields)
            ))

        validators = self.LOOKUP_FIELD_VALIDATORS.get(lookup_field, [])
        for validator in validators:
            try:
                validator(self.kwargs[self.lookup_url_kwarg])
            except ValidationError as e:
                raise ParseError('{lookup}: {message}'.format(lookup=lookup_field, message=u' '.join(e.messages)))
        return lookup_field

    def get_object(self):
        """
        Return the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.

        Note: due to need to inject decrypted identifier and hard to extend original function this override original one.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        lookup_field = self.lookup_field
        identifier = self.kwargs[lookup_url_kwarg]
        filter_kwargs = self.get_lookup_filters(lookup_field=lookup_field, identifier=identifier)
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_lookup_filters(self, lookup_field, identifier) -> Dict[str, Any]:
        if hasattr(self, 'LOOKUP_FIELD_MAPPERS') and lookup_field in self.LOOKUP_FIELD_MAPPERS:
            lookup_field, identifier = self.LOOKUP_FIELD_MAPPERS[lookup_field](identifier)

        return {lookup_field: identifier}

    def _get_permitted_lookup_fields(self) -> Generator[str, None, None]:
        for lookup_field in self.ALLOWED_LOOKUP_FIELDS:
            if isinstance(lookup_field, WithPermissions) and not lookup_field.has_permission(self.request.user):
                continue

            yield lookup_field

