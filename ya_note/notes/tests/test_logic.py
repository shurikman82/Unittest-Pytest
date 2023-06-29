from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.anonimous = User.objects.create(username='Аноним')
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'slug-new',
        }

    def test_user_can_create_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:add')
        notes_count_before = Note.objects.count()
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count_after = Note.objects.count()
        self.assertEqual((notes_count_after - notes_count_before), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        self.anonimous = Client()
        url = reverse('notes:add')
        notes_count_before = Note.objects.count()
        response = self.client.post(url, data=self.form_data)
        notes_count_after = Note.objects.count()
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual((notes_count_after - notes_count_before), 0)


class TestLogicSlug(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.client.force_login(self.author)
        notes_count_before = Note.objects.count()
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=self.author,
        )
        self.form_data['slug'] = self.note.slug
        response = self.client.post(url, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING),
        )
        self.assertEqual((notes_count_after - notes_count_before), 0)

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.client.force_login(self.author)
        self.form_data.pop('slug')
        notes_count_before = Note.objects.count()
        response = self.client.post(url, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual((notes_count_after - notes_count_before), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestEditDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-slug',
            author=cls.author,
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_author_can_edit_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.reader)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:delete', args=(self.note.slug,))
        notes_count_before = Note.objects.count()
        response = self.client.post(url)
        notes_count_after = Note.objects.count()
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual((notes_count_before - notes_count_after), 1)

    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.reader)
        url = reverse('notes:delete', args=(self.note.slug,))
        notes_count_before = Note.objects.count()
        response = self.client.post(url)
        notes_count_after = Note.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual((notes_count_before - notes_count_after), 0)
