# Lookup Fields

![Test package](https://github.com/innovationinit/drf-lookup-fields/actions/workflows/test-package.yml/badge.svg?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/innovationinit/drf-lookup-fields/badge.svg)](https://coveralls.io/github/innovationinit/drf-lookup-fields)

This package provides utils for changing lookup fields in requests to Django Rest Framework endpoints. It supports choosing lookup field for identifier of endpoint and identifiers used in related fields of serializers.

## Per field lookup usage

Data for field should be supplied in `Content-Lookup-Fields` HTTP header as base64 encoded json object where keys are serializer fields names (if nested use dotted notation) and values are intended lookup fields:
```json
{
  "some_field": "uuid",
  "other.nested.field": "pk",
}
```

### Field
```python
from lookup_fields.fields import CustomizableLookupRelatedField
from rest_framework import serializers


class Serializer(serializers.ModelSerializer):
    field = CustomizableLookupRelatedField(
        lookup_fields={
            'some_field': serializers.CharField(),
            'uuid': serializers.UUIDField(),
            'other_field': serializers.IntegerField(),
            'another_field_with_custom_filter_lookup_suffix': {
                'field': serializers.CharField(max_length=20),
                'filter_lookup_suffix': '__icontains',
            }
        },
        no_pk_lookup=True,
        default_lookup_field_name='uuid',
    )
```

default_lookup_field_name is 'pk', integer pk field is always added to lookup_fields. If you don't want this behavior set no_pk_lookup to True. Even then you can still add pk to lookup_fields when instantiate field.

You can specify optional parameters to lookup_fields by passing a dict instead of Field instance. Field has to be passed under 'field' key.

### Serializer

Serializers uses `CustomizableLookupRelatedField` as default related field.

```python
from lookup_fields.fields import CustomizableLookupRelatedField
from rest_framework import serializers


class Serializer(CustomizableLookupRelatedField):
    class Meta:
        model = SomeModel
        fields = (
            'relation',
        )
        extra_kwargs = {
            'relation': {
                'lookup_fields': {
                    'some_field': serializers.CharField(),
                },
            },
        }
```

## View mixin usage
Name of lookup field should be supplied in `Lookup-Field` HTTP header.

### View
```python
from lookup_fields.views import CustomizableLookupFieldMixin
from rest_framework.generics import GenericAPIView


class View(CustomizableLookupFieldMixin, GenericAPIView):
    ALLOWED_LOOKUP_FIELDS = [
        'pk',
        'uuid',
        'some_field',
        WithPermissions(
            'other_field',
            permissions=['some_app.can_use_other_field_as_lookup_field'],
        )
    ]
    LOOKUP_FIELD_VALIDATORS = {
        'some_field': [validator],
    }
```

## License
The Django Rest Framework Lookup Fields package is licensed under the [FreeBSD
License](https://opensource.org/licenses/BSD-2-Clause).
