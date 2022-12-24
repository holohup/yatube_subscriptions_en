from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class ProjectURLTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.authorized_client = Client()
        cls.authors_client = Client()
        cls.authorized_user = User.objects.create_user(username='HasNoName')
        cls.authorized_client.force_login(cls.authorized_user)
        cls.post_author = User.objects.create(username='TestAuthor')
        cls.authors_client.force_login(cls.post_author)

        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый текст',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Фокус-покус, ее уже нет',
            slug='test_group',
        )

        cls.unauthorized_user_available_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=(cls.group.slug,)):
                'posts/group_list.html',
            reverse('posts:profile', args=(cls.post_author.username,)):
                'posts/profile.html',
            reverse('posts:post_detail', args=(cls.post.id,)):
                'posts/post_detail.html'
        }

    def setUp(self):
        cache.clear()

    def test_unauthorized_pages_availability(self):
        """Доступность страниц, не требующих авторизации,
        неавторизованному пользователю."""

        for url in self.unauthorized_user_available_pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK, url)

    def test_unauthorized_templates_correctness(self):
        """Доступность правильных шаблонов неавторизованному
        пользователю."""

        for address, tmpl in self.unauthorized_user_available_pages.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK, address)
                self.assertTemplateUsed(response, tmpl)

    def test_edit_other_persons_post_redirect(self):
        """Работа редиректа при попытке редактировать чужой пост."""

        response = self.authorized_client.get(
            reverse('posts:post_edit', args=(self.post.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,))
        )

    def test_unauthorized_user_private_pages_redirect(self):
        """Работа редиректа для неавторизованного пользователя
        при попытке зайти на приватные страницы."""

        login_url = reverse('users:login')
        pages = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=(self.post.id,))
        }
        for url in pages:
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(
                    response, f'{login_url}?next={url}'
                )

    def test_edit_and_create_availability_for_post_author(self):
        """Доступность страниц при попытке авторизованного пользователя
        создавать пост и редактировать свой пост."""

        pages = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=(self.post.id,))
        }
        for url in pages:
            with self.subTest(url=url):
                response = self.authors_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authors_create_and_edit_templates(self):
        """Правильность шаблонов при попытке авторизованного пользователя
        создавать новый пост, или редактировать свой пост."""

        correct_templates = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args=(self.post.id,)):
                'posts/create_post.html',
        }
        for address, tmpl in correct_templates.items():
            with self.subTest(address=address):
                response = self.authors_client.get(address)
                self.assertTemplateUsed(response, tmpl)
                self.assertEqual(response.status_code, HTTPStatus.OK)
