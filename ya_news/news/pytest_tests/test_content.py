import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from datetime import timedelta

from news.models import Comment

User = get_user_model()


@pytest.mark.django_db
def test_news_count(client, all_news):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count, settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, all_news):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates, sorted_dates


def test_comments_order(client, author, news, comment):
    url = reverse('news:detail', args=(news.id,))
    now = timezone.now()
    for index in range(2):
        comment = Comment.objects.create(
                news=news, author=author, text=f'Tекст {index}',
            )
        comment.created = now + timedelta(days=index)
        comment.save()
        response = client.get(url)
        assert 'news' in response.context
        news = response.context['news']
        all_comments = news.comment_set.all()
        assert all_comments[0].created < all_comments[1].created


def test_anonymous_client_has_no_form(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context


def test_authorized_client_has_form(author_client, news):
    url = reverse('news:detail', args=(news.id,))
    response = author_client.get(url)
    assert 'form' in response.context
