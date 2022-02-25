"""Fields with customizable lookup fields."""

import base64
import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ParseError


__all__ = [
    'CustomizableLookupRelatedField',
    'CustomizableLookupManyRelatedField',
]


class SetupRequiredAttribute(object):

    def __init__(self, name, start_value=None):
        self._name = '_store_{}'.format(name)
        self._start_value = start_value

    def __get__(self, instance, owner):
        """Perform CustomizableLookupRelatedField setup if it's not already done."""
        if not instance:
            return self

        if not instance._setup_done:  # noqa
            try:
                instance.setup_field_lookup()
                instance._setup_exception = None
            except Exception as e:
                instance._setup_exception = e

        if instance._setup_exception is not None:
            raise instance._setup_exception

        return getattr(instance, self._name, self._start_value)

    def __set__(self, instance, value):
        if not instance:
            return

        setattr(instance, self._name, value)


class CustomizableLookupRelatedField(serializers.RelatedField):

    """RelatedField using supplied in header field for lookup and read value.
    Default lookup field is integer pk.
    """

    default_error_messages = {
        'required': _("This field is required."),
        'does_not_exist': _("Invalid {lookup_field} \"{value}\" - object does not exist."),
        'incorrect_type': _("Incorrect type. Expected {lookup_field} value, received {data_type}."),
        'not_allowed_field': _(
            "Error in content lookup fields header. "
            "Field {lookup_field} is not allowed lookup field for {field_name}. Only {allowed_fields} are allowed."
        ),
        'invalid_header_data': _("Invalid content of content lookup fields header!"),
    }

    LOOKUP_FIELDS_FIELD_KEY = 'field'
    LOOKUP_FIELDS_FILTER_LOOKUP_SUFFIX_KEY = 'filter_lookup_suffix'
    LOOKUP_FIELDS_AUTO = '__auto__'
    LOOKUP_FIELDS_AUTO_TO_REPRESENTATION_ATTR = 'pk'

    lookup_field_name = SetupRequiredAttribute('lookup_field_name')
    lookup_field = SetupRequiredAttribute('lookup_field')
    filter_lookup_suffix = SetupRequiredAttribute('filter_lookup_suffix')
    full_field_path = SetupRequiredAttribute('full_field_path')
    root_parent = SetupRequiredAttribute('root_parent')

    def __init__(self, **kwargs):
        self._setup_done = False
        self._setup_exception = None
        self.no_pk_lookup = kwargs.pop('no_pk_lookup', False)
        self.lookup_fields = self.get_default_lookup_fields(override=kwargs.pop('lookup_fields', {}))
        self.default_lookup_field_name = kwargs.pop('default_lookup_field_name', 'pk')
        self.http_header_name = kwargs.pop(
            'http_header_name',
            getattr(settings, 'LOOKUP_FIELDS_CONTENT_LOOKUP_FIELDS_HEADER_DEFAULT_NAME', 'HTTP_CONTENT_LOOKUP_FIELDS'),
        )
        super(CustomizableLookupRelatedField, self).__init__(**kwargs)

    def use_pk_only_optimization(self):
        return self.lookup_field_name == 'pk'

    def get_instance(self, value):
        """Method for easier instance getting overriding. Should return instance or raise proper DoesNotExist."""
        return self.get_queryset().get(**self.get_instance_filter_kwargs(value))

    def to_internal_value(self, data):
        data = self.lookup_field.to_internal_value(data)
        try:
            return self.get_instance(data)
        except ObjectDoesNotExist:
            self.fail(
                'does_not_exist',
                lookup_field=self.lookup_field_name,
                value=data,
            )
        except (TypeError, ValueError):
            self.fail(
                'incorrect_type',
                lookup_field=self.lookup_field_name,
                data_type=type(data).__name__,
            )

    def to_representation(self, value):
        value = getattr(
            value,
            self.LOOKUP_FIELDS_AUTO_TO_REPRESENTATION_ATTR if self.lookup_field_name == self.LOOKUP_FIELDS_AUTO else self.lookup_field_name,
        )
        if value is not None:
            return self.lookup_field.to_representation(value)
        return None

    def setup_field_lookup(self):
        if self.parent and self.parent.parent is not None or self._is_root_parent(self.parent):
            self._setup_done = True
            full_field_path = [] if not self.field_name else [self.field_name]
            parent = self.parent
            self._append_if_not_empty(full_field_path, parent.field_name)

            while parent.parent:
                parent = parent.parent
                self._append_if_not_empty(full_field_path, parent.field_name)

            self.full_field_path = '.'.join(reversed(full_field_path))
            self.root_parent = parent

            self.lookup_field_name = self.get_lookup_field_name()
            if isinstance(self.lookup_fields[self.lookup_field_name], dict):
                self.lookup_field = self.lookup_fields[self.lookup_field_name][self.LOOKUP_FIELDS_FIELD_KEY]
                self.filter_lookup_suffix = self.lookup_fields[self.lookup_field_name].get(
                    self.LOOKUP_FIELDS_FILTER_LOOKUP_SUFFIX_KEY,
                    None,
                )
            else:
                self.lookup_field = self.lookup_fields[self.lookup_field_name]

    def validate_empty_values(self, data):
        if self.lookup_field_name == self.LOOKUP_FIELDS_AUTO:
            return True, None
        return super().validate_empty_values(data)

    ##########
    # Helpers
    ##########

    def get_lookup_field_name(self):
        lookup_field_name = self.get_data_from_request_header().get(self.full_field_path, self.default_lookup_field_name)
        if lookup_field_name not in self.lookup_fields:
            self.fail(
                'not_allowed_field',
                lookup_field=lookup_field_name,
                field_name=self.full_field_path,
                allowed_fields=', '.join(self.lookup_fields.keys()),
            )
        return lookup_field_name

    def get_data_from_request_header(self):
        request = self.get_request()
        if request and self.http_header_name in request.META:
            try:
                data = json.loads(base64.b64decode(request.META[self.http_header_name]).decode('utf-8'))
                if isinstance(data, dict):
                    return data
                raise TypeError()
            except (ValueError, TypeError):
                raise ParseError(self.default_error_messages['invalid_header_data'])
        return {}

    def get_request(self):
        """Get request from context of root parent."""
        if self.root_parent and hasattr(self.root_parent, '_context'):
            return self.root_parent._context.get('request')  # noqa

    def get_default_lookup_fields(self, override=None):
        fields = {
            'pk': serializers.IntegerField(),
        } if not self.no_pk_lookup else {}
        if override:
            fields.update(override)
        return fields

    def get_instance_filter_kwargs(self, value):
        lookup_suffix = self.filter_lookup_suffix or ''
        return {
            '{}{}'.format(self.lookup_field_name, lookup_suffix): value
        }

    @staticmethod
    def _append_if_not_empty(collection, element):
        if element:
            collection.append(element)

    @staticmethod
    def _is_root_parent(parent):
        if parent and not parent.parent and getattr(parent, '_context', None):
            return True
        return False


class CustomizableLookupManyRelatedField(serializers.ManyRelatedField):

    """Left for backwards compatibility. Deprecated"""
