import random
import shutil
import tempfile

from faker import Faker
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, Follow, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectViewsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.authorized_client = Client()
        cls.authorized_user = User.objects.create_user(
            username='InsaneTester')
        cls.authorized_client.force_login(cls.authorized_user)
        cls.test_group = Group.objects.create(
            title='Тестовая группа для поста',
            description='Дни ее скоротечны',
            slug='test_group',
        )
        cls.test_post = Post.objects.create(
            author=cls.authorized_user,
            text='Тестовый текстовый пост',
            group=cls.test_group
        )

    @classmethod
    def setUp(cls):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_index_correct_context(self):
        """Правильность контекста главной страницы."""

        response = self.client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        page_content = response.context['page_obj']
        self.assertEqual(page_content[0], self.test_post)

    def test_group_list_correct_context(self):
        """Правильность контекста списка постов группы."""

        response = self.client.get(
            reverse(
                'posts:group_list', args=(self.test_group.slug,)
            )
        )
        self.assertIn('group', response.context)
        self.assertIn('page_obj', response.context)
        page_content = response.context['page_obj']
        group_received = response.context['group']
        self.assertEqual(group_received, self.test_group)
        self.assertEqual(page_content[0], self.test_post)

    def test_profile_correct_context(self):
        """Правильность контекста профиля пользователя."""

        response = self.client.get(
            reverse('posts:profile', args=(self.authorized_user.username,))
        )
        self.assertIn('author', response.context)
        self.assertIn('page_obj', response.context)
        page_author = response.context.get('author')
        page_content = response.context.get('page_obj')
        self.assertEqual(page_author, self.authorized_user)
        self.assertEqual(page_content[0], self.test_post)

    def test_post_detail_correct_context(self):
        """Контекст страницы поста."""

        response = self.client.get(
            reverse('posts:post_detail', args=(self.test_post.id,))
        )
        self.assertIn('post', response.context)
        received_post = response.context['post']
        self.assertEqual(received_post, self.test_post)

    def test_create_and_edit_post_correct_context(self):
        """Контекст страницы создания/редактирования поста
        для авторизованного пользователя."""

        pages = {
            'create': reverse('posts:post_create'),
            'edit': reverse('posts:post_edit', args=(self.test_post.id,))
        }
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(pages[page])
                self.assertIn('form', response.context)
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                if 'is_edit' in response.context:
                    self.assertTrue(response.context['is_edit'])

    def test_testpost_not_in_an_unappropriated_group(self):
        """Не попал ли пост в неподходящую группу."""

        other_group = Group.objects.create(
            title='Группа для тестирования',
            description='В этой группе не должно быть искомого поста',
            slug='test_group_2'
        )
        fake = Faker('ru_RU')
        Post.objects.bulk_create([(Post(
            author=self.authorized_user,
            text=fake.text(),
            group=other_group
        )) for _ in range(1, settings.POSTS_TO_DISPLAY - 1)])
        response = self.client.get(
            reverse('posts:group_list', args=(other_group.slug,))
        )
        page_obj = response.context['page_obj']
        self.assertNotIn(self.test_post, page_obj)

    def test_posts_with_images_exist_in_page_context(self):
        """Создает пост с картинкой и проверяет, попала ли картинка
        в контекст страниц: главной, профайла, группы и поста."""

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        fake = Faker()
        uploaded = SimpleUploadedFile(
            name=fake.file_name(extension='gif'),
            content=small_gif,
            content_type='image/gif'
        )
        imagefile = f'posts/{uploaded.name}'
        test_post = Post.objects.create(
            image=uploaded,
            text=fake.text(),
            group=self.test_group,
            author=self.authorized_user
        )
        paginated_pages_to_check = {
            reverse('posts:index'),
            reverse('posts:profile', args=(self.authorized_user.username,)),
            reverse('posts:group_list', args=(self.test_group.slug,)),
        }
        response = self.client.get(
            reverse('posts:post_detail', args=(test_post.id,))
        )
        self.assertEqual(response.context['post'].image, imagefile)
        for page in paginated_pages_to_check:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    response.context['page_obj'][0].image,
                    imagefile,
                    page
                )


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.fake = Faker('ru_RU')
        cls.number_of_posts = random.randint(
            settings.POSTS_TO_DISPLAY + 1, 2 * settings.POSTS_TO_DISPLAY - 1
        )
        cls.authorized_user = User.objects.create_user(username='MrNobody')
        cls.group = Group.objects.create(
            title='Тестовая группа для постов',
            description='Группа Ли',
            slug='test_group'
        )
        Post.objects.bulk_create([(Post(
            author=cls.authorized_user,
            text=cls.fake.text(),
            group=cls.group
        )) for _ in range(cls.number_of_posts)])

    @classmethod
    def setUp(cls):
        cache.clear()

    def test_paginator_on_all_paginated_pages(self):
        """Проверяет все страницы с пагинатором:
        -Количество постов на первой должно равняться максимальному
        -Количество постов на второй должно равняться остатку."""

        pages = {
            1: settings.POSTS_TO_DISPLAY,
            2: self.number_of_posts % settings.POSTS_TO_DISPLAY
        }
        urls = {
            'index': reverse('posts:index'),
            'group_list': reverse('posts:group_list', args=(self.group.slug,)),
            'profile': reverse('posts:profile', args=(self.authorized_user,)),
        }
        for url in urls:
            for page, posts in pages.items():
                with self.subTest(posts=posts):
                    response = self.client.get(urls[url], data={'page': page})
                    self.assertEqual(
                        len(response.context['page_obj']), posts)


class SubscriptionsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.fake = Faker('ru_RU')
        cls.user_a = User.objects.create_user(username='User_A')
        cls.user_b = User.objects.create_user(username='User_B')
        cls.author = User.objects.create_user(username='Author')
        cls.client_a = Client()
        cls.client_b = Client()
        cls.client_author = Client()
        cls.client_a.force_login(cls.user_a)
        cls.client_b.force_login(cls.user_b)
        cls.client_author.force_login(cls.author)
        cls.index_url = reverse('posts:follow_index')
        cls.follow_url = reverse(
            'posts:profile_follow', args=(cls.author,)
        )
        cls.unfollow_url = reverse(
            'posts:profile_unfollow', args=(cls.author,)
        )
        cls.group = Group.objects.create(
            title='Тестовая группа для постов',
            description='Подпишись, жми колокольчик',
            slug='test_group'
        )
        Post.objects.bulk_create([(Post(
            author=cls.author,
            text=cls.fake.text(),
            group=cls.group
        )) for _ in range(random.randint(1, 10))])

    @classmethod
    def setUp(cls):
        cache.clear()

    def test_post_visibility_after_post_creation(self):
        """Создает пост и проверяет, что он виден для подписчика
        и не виден для неподписанного пользователя."""

        Follow.objects.create(user=self.user_a, author=self.author)
        test_post = Post.objects.create(
            author=self.author,
            text=self.fake.text(),
            group=self.group
        )
        response_a = self.client_a.get(self.index_url)
        response_b = self.client_b.get(self.index_url)
        page_obj_a = response_a.context['page_obj']
        page_obj_b = response_b.context['page_obj']
        self.assertEqual(test_post, page_obj_a[0])
        self.assertNotIn(test_post, page_obj_b)

    def test_post_visibility_after_subscription_creation(self):
        """Проверяет, что пост появляется на странице подписок,
        если пользователь подписывается на автора и не появляется,
        если не подписывается. Подписчик user_a подписывается
        на author, user_b - нет."""

        response_a = self.client_a.get(self.index_url)
        response_b = self.client_b.get(self.index_url)
        test_post = Post.objects.create(
            author=self.author,
            text=self.fake.text(),
            group=self.group
        )
        self.assertNotIn(test_post, response_a.context['page_obj'])
        self.assertNotIn(test_post, response_b.context['page_obj'])
        Follow.objects.create(user=self.user_a, author=self.author)
        response_a = self.client_a.get(self.index_url)
        response_b = self.client_b.get(self.index_url)
        self.assertEqual(test_post, response_a.context['page_obj'][0])
        self.assertNotIn(test_post, response_b.context['page_obj'])

    def test_subscriptions_availability(self):
        """Проверка создания подписки."""

        self.assertFalse(
            Follow.objects.filter(
                user=self.user_a, author=self.author
            ).exists()
        )
        subscriptions = Follow.objects.count()
        response = self.client_a.get(self.follow_url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.author,))
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_a, author=self.author
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), subscriptions + 1)

    def test_unsubscriptions_availability(self):
        """Проверка удаления подписки."""

        Follow.objects.create(user=self.user_a, author=self.author)
        subscriptions = Follow.objects.count()
        response = self.client_a.get(self.unfollow_url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.author,))
        )
        self.assertEqual(Follow.objects.count(), subscriptions - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_a, author=self.author
            ).exists()
        )


class ProjectCacheTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.authorized_client = Client()
        cls.authorized_user = User.objects.create_user(
            username='InsaneTester')
        cls.authorized_client.force_login(cls.authorized_user)
        cls.test_group = Group.objects.create(
            title='Тестовая группа для поста',
            description='Дни ее скоротечны',
            slug='test_group',
        )
        cls.test_post = Post.objects.create(
            author=cls.authorized_user,
            text='Тестовый текстовый пост',
            group=cls.test_group
        )

    def setUp(self):
        cache.clear()

    def test_index_cache_is_working(self):
        """Проверяет, кэшируется ли главная страница"""

        index_url = reverse('posts:index')
        test_post = Post.objects.create(
            author=self.authorized_user,
            text='Матушка возьмет ведро, молча наберет воды.',
            group=self.test_group
        )

        response = self.client.get(index_url)
        first_content = response.content
        self.assertEqual(test_post, response.context['page_obj'][0])
        test_post.delete()
        response = self.client.get(index_url)
        self.assertEqual(response.content, first_content)
        cache.clear()
        response = self.client.get(index_url)
        self.assertNotEqual(response.content, first_content)
