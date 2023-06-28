from http import HTTPStatus

from pytest_django.asserts import assertRedirects, assertFormError

from django.contrib.auth import get_user_model
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

User = get_user_model()


def test_anonymous_user_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_can_create_comment(admin_client, admin_user, form_data, news):
    url = reverse('news:detail', args=(news.id,))
    response = admin_client.post(url, data=form_data)
    redirect = f'{url}#comments'
    assertRedirects(response, redirect)
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == 'Новый текст'
    assert comment.news == news
    assert comment.author == admin_user


def test_user_cant_use_bad_words(admin_client, news):
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(author_client, comment, news):
    url = reverse('news:delete', args=(comment.id,))
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = news_url + '#comments'
    response = author_client.delete(url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_cant_delete_comment_of_another_user(admin_client, comment):
    url = reverse('news:delete', args=(comment.id,))
    response = admin_client.delete(url)
    assert response.status_code, HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_author_can_edit_comment(author_client, comment, news, form_data):
    url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(url, data=form_data)
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = news_url + '#comments'
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == 'Новый текст'


def test_user_cant_edit_comment_of_another_user(
        admin_client, comment, form_data):
    url = reverse('news:edit', args=(comment.id,))
    response = admin_client.post(url, data=form_data)
    assert response.status_code, HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == 'Текст комментария'
