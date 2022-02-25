# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    unicode_literals,
)

from lookup_fields.fields import CustomizableLookupRelatedField
from lookup_fields.serializers import CustomizableLookupFieldsModelSerializer
from rest_framework import serializers

from .models import (
    Author,
    Book,
    BookCopy,
    Country,
)


class BookCopySerializer(CustomizableLookupFieldsModelSerializer):

    class Meta:
        model = BookCopy
        fields = (
            'id',
            'uuid',
            'book',
        )
        extra_kwargs = {
            'book': {
                'lookup_fields': {
                    'isbn': serializers.CharField(max_length=20),
                    'uuid': serializers.UUIDField(format='hex'),
                    'title': {
                        'field': serializers.CharField(max_length=200),
                        'filter_lookup_suffix': '__icontains',
                    },
                }
            },
            'uuid': {
                'format': 'hex',
            },
        }


class BookCopySerializerWithManuallyDeclaredField(serializers.ModelSerializer):

    book = CustomizableLookupRelatedField(
        lookup_fields={
            'isbn': serializers.CharField(max_length=20),
            'uuid': serializers.UUIDField(format='hex'),
            'title': {
                'field': serializers.CharField(max_length=200),
                'filter_lookup_suffix': '__icontains',
            },
        },
        queryset=Book.objects.all(),
    )

    class Meta:
        model = BookCopy
        fields = (
            'id',
            'uuid',
            'book',
        )
        extra_kwargs = {
            'uuid': {
                'format': 'hex',
            },
        }


class BookSerializer(CustomizableLookupFieldsModelSerializer):
    copies = BookCopySerializer(many=True, read_only=True)

    class Meta:
        model = Book
        read_only = (
            'copies',
        )
        fields = (
            'id',
            'uuid',
            'isbn',
            'title',
            'weight',
            'author',
            'country_of_origin',
        ) + read_only

        extra_kwargs = {
            'author': {
                'lookup_fields': {
                    'uuid': serializers.UUIDField(format='hex'),
                },
                'default_lookup_field_name': 'uuid',
                'no_pk_lookup': True,
            },
            'uuid': {
                'format': 'hex',
            },
            'country_of_origin': {
                'lookup_fields': {
                    '__auto__': serializers.IntegerField(),
                }
            }
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.fields.get('country_of_origin').lookup_field_name == CustomizableLookupRelatedField.LOOKUP_FIELDS_AUTO:
            try:
                isbn_code = attrs['isbn'].split('-')[1]
            except IndexError:
                attrs['country_of_origin'] = None
            else:
                attrs['country_of_origin'] = Country.objects.filter(isbn_code=isbn_code).first()
        return attrs


class AuthorSerializer(serializers.ModelSerializer):
    books = BookSerializer(many=True)

    class Meta:
        model = Author
        fields = (
            'id',
            'uuid',
            'first_name',
            'last_name',
            'books',
        )
        extra_kwargs = {
            'uuid': {
                'format': 'hex',
            },
        }
