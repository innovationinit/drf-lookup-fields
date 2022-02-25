"""Serializers with customizable lookup fields."""

from rest_framework import serializers

from .fields import CustomizableLookupRelatedField


class CustomizableLookupFieldsModelSerializer(serializers.ModelSerializer):

    """ModelSerializer with default related field CustomizableLookupRelatedField."""

    serializer_related_field = CustomizableLookupRelatedField


class CustomizableLookupFieldsListSerializer(serializers.ListSerializer):

    """Left for backwards compatibility. Deprecated"""
