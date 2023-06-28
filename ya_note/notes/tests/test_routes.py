from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.notes = Note.objects.create(
            title='Заголовок', text='Текст', author=cls.author,
        )

    def test_page_avilability_for_anonimous_user(self):
        urls = ('notes:home', 'users:login', 'users:logout', 'users:signup')
        for name in urls:
            url = reverse(name)
            response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        users_statuses = (
            (self.reader, HTTPStatus.OK),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:list', 'notes:add', 'notes:success'):
                with self.subTest(user=user, name=name):
                    url = reverse(name)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_for_auth_users(self):
        urls = ('notes:detail', 'notes:edit', 'notes:delete')
        self.client.force_login(self.reader)
        for name in urls:
            url = reverse(name, args=(self.notes.slug,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_pages_availability_for_author(self):
        urls = ('notes:detail', 'notes:edit', 'notes:delete')
        self.client.force_login(self.author)
        for name in urls:
            url = reverse(name, args=(self.notes.slug,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirects(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.notes.slug,)),
            ('notes:edit', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
