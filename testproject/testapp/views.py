from django.core.exceptions import ValidationError

from lookup_fields.views import CustomizableLookupFieldMixin
from lookup_fields.permissions import WithPermissions
from rest_framework.generics import GenericAPIView

from .models import Book


def raise_validation_error(*args, **kwargs):
    raise ValidationError('Error')


class BookAPIView(CustomizableLookupFieldMixin, GenericAPIView):

    queryset = Book.objects.all()
    LOOKUP_FIELD_VALIDATORS = {
        'title': [raise_validation_error],
    }
    ALLOWED_LOOKUP_FIELDS = [
        'pk',
        'uuid',
        'title',
        WithPermissions('isbn', permissions=['testapp.can_use_isbn_as_lookup_field'])
    ]
