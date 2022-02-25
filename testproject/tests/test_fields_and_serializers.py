# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    unicode_literals,
)

from decimal import Decimal

from django.test.testcases import TestCase

from rest_framework.exceptions import (
    ParseError,
    ValidationError,
)

from testapp.models import (
    Author,
    Book,
    BookCopy,
    Country,
)
from testapp.serializers import (
    AuthorSerializer,
    BookSerializer,
    BookCopySerializer,
    BookCopySerializerWithManuallyDeclaredField,
)
from .utils import (
    fake_request_factory,
    get_different_uuid,
)


FakeRequest = fake_request_factory('HTTP_CONTENT_LOOKUP_FIELDS')


class FieldAndSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(first_name='John', last_name='Smith')
        cls.book = Book.objects.create(
            author=cls.author,
            title='Some book',
            isbn='123-4-56-789012-3',
            weight=Decimal('0.5'),
        )
        cls.book_copy = BookCopy.objects.create(book=cls.book)

    def test_serialization__all_default(self):
        serializer = AuthorSerializer(self.author, context={'request': FakeRequest()})
        data = serializer.data

        self.assertEqual(data['books'][0]['author'], self.author.uuid.hex)
        self.assertEqual(data['books'][0]['copies'][0]['book'], self.book.pk)

    def test_serialization__set_in_header(self):
        serializer = AuthorSerializer(self.author, context={'request': FakeRequest({'books.copies.book': 'isbn'})})
        data = serializer.data

        self.assertEqual(data['books'][0]['author'], self.author.uuid.hex)
        self.assertEqual(data['books'][0]['copies'][0]['book'], self.book.isbn)

        serializer = AuthorSerializer(self.author, context={'request': FakeRequest({'books.copies.book': 'title'})})
        data = serializer.data

        self.assertEqual(data['books'][0]['author'], self.author.uuid.hex)
        self.assertEqual(data['books'][0]['copies'][0]['book'], self.book.title)

        serializer = AuthorSerializer(self.author, context={'request': FakeRequest({'books.copies.book': 'uuid'})})
        data = serializer.data

        self.assertEqual(data['books'][0]['author'], self.author.uuid.hex)
        self.assertEqual(data['books'][0]['copies'][0]['book'], self.book.uuid.hex)

        serializer = AuthorSerializer(self.author, context={'request': FakeRequest({
            'books.copies.book': 'pk',
            'book.author': 'uuid',
        })})
        data = serializer.data

        self.assertEqual(data['books'][0]['author'], self.author.uuid.hex)
        self.assertEqual(data['books'][0]['copies'][0]['book'], self.book.pk)

    def test_serialization__not_existent_field(self):
        serializer = AuthorSerializer(self.author, context={'request': FakeRequest({'books.copies.book': 'non_existent_field'})})

        with self.assertRaises(ValidationError):
            serializer.data

    def test_serialization__not_allowed_field(self):
        serializer = AuthorSerializer(self.author, context={'request': FakeRequest({'books.author': 'pk'})})

        with self.assertRaises(ValidationError):
            serializer.data

    def test_serialization__invalid_data_in_header(self):
        serializer = AuthorSerializer(self.author, context={'request': FakeRequest(['bad', 'data'])})

        with self.assertRaises(ParseError):
            serializer.data

        serializer = AuthorSerializer(self.author, context={'request': FakeRequest(raw_content='totally invalid data')})

        with self.assertRaises(ParseError):
            serializer.data

    def test_creating__all_default(self):
        serializer = BookCopySerializer(
            data={'book': self.book.pk},
            context={'request': FakeRequest()},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

    def test_creating__set_in_header(self):
        serializer = BookCopySerializer(
            data={'book': self.book.uuid.hex},
            context={'request': FakeRequest({'book': 'uuid'})},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

        serializer = BookCopySerializer(
            data={'book': self.book.isbn},
            context={'request': FakeRequest({'book': 'isbn'})},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

        serializer = BookCopySerializer(
            data={'book': self.book.title},
            context={'request': FakeRequest({'book': 'title'})},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

    def test_creating__set_in_header__serializer_with_manually_declared_field(self):
        serializer = BookCopySerializerWithManuallyDeclaredField(
            data={'book': self.book.uuid.hex},
            context={'request': FakeRequest({'book': 'uuid'})},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

        serializer = BookCopySerializerWithManuallyDeclaredField(
            data={'book': self.book.isbn},
            context={'request': FakeRequest({'book': 'isbn'})},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

        serializer = BookCopySerializerWithManuallyDeclaredField(
            data={'book': self.book.title},
            context={'request': FakeRequest({'book': 'title'})},
        )
        serializer.is_valid(raise_exception=True)
        book_copy = serializer.save()

        self.assertEqual(book_copy.book, self.book)

    def test_creating__invalid_identifier_value(self):
        serializer = BookCopySerializer(
            data={'book': 'invalid_value'},
            context={'request': FakeRequest({'book': 'uuid'})},
        )

        self.assertFalse(serializer.is_valid())

    def test_creating__not_found(self):
        serializer = BookCopySerializer(
            data={'book': get_different_uuid(self.book.uuid)},
            context={'request': FakeRequest({'book': 'uuid'})},
        )

        self.assertFalse(serializer.is_valid())

    def test_creating__not_allowed_field(self):
        serializer = BookCopySerializer(
            data={'book': self.book.weight},
            context={'request': FakeRequest({'book': 'weight'})},
        )

        self.assertFalse(serializer.is_valid())

    def test_creating__not_allowed_field__many(self):
        serializer = BookCopySerializer(
            data=[
                {'book': self.book.weight},
                {'book': 12},
            ],
            context={'request': FakeRequest({'book': 'weight'})},
            many=True,
        )

        self.assertFalse(serializer.is_valid())

    def test_creating__invalid_identifier_type(self):
        serializer = BookCopySerializer(
            data={'book': self.book.pk},
            context={'request': FakeRequest({'book': 'uuid'})},
        )

        self.assertFalse(serializer.is_valid())

    def test_creating__auto_field(self):
        country = Country.objects.create(name='Poland', isbn_code='83')
        author = Author.objects.create(first_name='John', last_name='Nowak')
        serializer = BookSerializer(
            data={
                'isbn': '978-83-01-00000-1',
                'title': 'My book',
                'weight': 100,
                'author': author.uuid,
            },
            context={'request': FakeRequest({'country_of_origin': '__auto__'})},
        )
        serializer.is_valid(raise_exception=True)
        book = serializer.save()

        self.assertEqual(book.country_of_origin, country)
