# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    unicode_literals,
)

import uuid

from django.db import models


class CommonModel(models.Model):

    uuid = models.UUIDField(unique=True, editable=False)

    class Meta:
        abstract = True

    def save(self, **kwargs):
        if self.uuid is None:
            new_uuid = uuid.uuid4()
            while self.__class__.objects.filter(uuid=new_uuid).exists():
                new_uuid = uuid.uuid4()
            self.uuid = new_uuid
        return super(CommonModel, self).save(**kwargs)


class Country(CommonModel):

    name = models.CharField(max_length=100)
    isbn_code = models.CharField(max_length=10, unique=True)


class BookCopy(CommonModel):

    book = models.ForeignKey('testapp.Book', related_name='copies', on_delete=models.CASCADE)


class Book(CommonModel):

    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    author = models.ForeignKey('testapp.Author', related_name='books', on_delete=models.CASCADE)
    country_of_origin = models.ForeignKey('testapp.Country', on_delete=models.PROTECT, null=True)

    class Meta:
        permissions = (
            ('can_use_isbn_as_lookup_field', 'Can use isbn as lookup field'),
        )


class Author(CommonModel):

    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
