from decimal import Decimal

from django.contrib.auth.models import (
    Permission,
    User,
)
from django.test.testcases import TestCase

from rest_framework.exceptions import ParseError

from testapp.models import (
    Author,
    Book,
)
from testapp.views import BookAPIView
from .utils import fake_request_factory


FakeRequest = fake_request_factory('HTTP_LOOKUP_FIELD')


class CustomizableLookupFieldMixinTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.book = Book.objects.create(
            author=Author.objects.create(first_name='John', last_name='Smith'),
            title='Some book',
            isbn='123-4-56-789012-3',
            weight=Decimal('0.1'),
        )
        cls.user = User.objects.create(username='test_user')

    def test_retrieving(self):
        view = BookAPIView()
        view.kwargs = {'identifier': self.book.pk}
        view.request = FakeRequest(raw_content='pk', user=self.user)

        self.assertEqual(view.get_object(), self.book)

        view.kwargs = {'identifier': self.book.uuid.hex}
        view.request = FakeRequest(raw_content='uuid', user=self.user)

        self.assertEqual(view.get_object(), self.book)

    def test_retrieving__field_with_permissions(self):
        view = BookAPIView()
        view.kwargs = {'identifier': self.book.isbn}
        view.request = FakeRequest(raw_content='isbn', user=self.user)

        with self.assertRaises(ParseError):
            view.get_object()

        user = User.objects.create(username='test_user2')
        user.user_permissions.add(
            Permission.objects.get(codename='can_use_isbn_as_lookup_field')
        )
        view.request = FakeRequest(raw_content='isbn', user=user)

        self.assertEqual(view.get_object(), self.book)

    def test_retrieving__not_allowed_field(self):
        view = BookAPIView()
        view.kwargs = {'identifier': self.book.author}
        view.request = FakeRequest(raw_content='author', user=self.user)

        with self.assertRaises(ParseError):
            view.get_object()

    def test_retrieving__validator_fail(self):
        view = BookAPIView()
        view.kwargs = {'identifier': self.book.title}
        view.request = FakeRequest(raw_content='title', user=self.user)

        with self.assertRaises(ParseError):
            view.get_object()
