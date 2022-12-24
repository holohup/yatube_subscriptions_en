from http import HTTPStatus
import shutil
import tempfile

from faker import Faker
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from ..models import Post, User, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='FormTester')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Старый пес сторожил гладиолусы',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_creation_by_an_authorized_user(self):
        """Пост создается авторизованным пользователем при отправке
        валидной формы."""

        fake = Faker('ru_RU')
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name=fake.file_name(extension='gif'),
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': fake.text(),
            'image': uploaded,
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.first()
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group, self.group)
        imagefile = f'posts/{uploaded.name}'
        self.assertTrue(last_post.image)
        self.assertEqual(last_post.image, imagefile)
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.user,))
        )

    def test_edit_post_by_an_authorized_user(self):
        """Автор поста может его редактировать."""

        test_post = Post.objects.create(
            author=self.user,
            text='И ей шептал: "С надеждой вдаль гляди!"',
            group=self.group
        )
        new_group = Group.objects.create(
            title='Группа для редактирования',
            slug='test_edit_group',
            description='Сюда попадет пост, если его удастся отредактировать',
        )
        post_count = Post.objects.count()
        text = 'Теплый ветер ему гладил волосы'
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(test_post.id,)),
            data={
                'text': text,
                'group': new_group.id,
            },
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        test_post.refresh_from_db()
        self.assertEqual(test_post.text, text)
        self.assertEqual(test_post.group, new_group)
        self.assertEqual(test_post.author, self.user)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(test_post.id,))
        )

    def test_edit_post_by_authorized_nonauthor(self):
        """Авторизованный юзер не может редактировать чужой пост."""

        text = 'И ей шептал: "С надеждой вдаль гляди!"'
        test_post = Post.objects.create(
            author=self.user,
            text=text,
            group=self.group
        )
        other_user = User.objects.create_user(username='BruteForcer')
        other_authorized_client = Client()
        other_authorized_client.force_login(other_user)
        response = other_authorized_client.post(
            reverse('posts:post_edit', args=(test_post.id,)),
            data={
                'text': 'At First I was afraid, I was petrified',
                'group': '',
            },
            follow=True
        )
        self.assertEqual(test_post.text, text)
        self.assertEqual(test_post.group, self.group)
        self.assertEqual(test_post.author, self.user)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(test_post.id,))
        )

    def test_post_creation_by_an_unauthorized_user(self):
        """Попытка создать пост неавторизованным юзером."""

        login_url = reverse('users:login')
        url = reverse('posts:post_create')
        post_count = Post.objects.count()
        response = self.client.post(
            url,
            data={
                'text': 'Товарищ, нам ехать далёко!', 'group': self.group.id
            },
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_comment_by_an_authorized_user(self):
        """Проверяем, что авторизованный юзер может оставить
        комментарий и что после успешной отправки комментарий
        появляется на странице поста."""

        text = 'Никогда бы не подумал, шикарно!'
        comment_count = Comment.objects.count()
        post_detail_url = reverse('posts:post_detail', args=(self.post.id,))
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': text, 'post': self.post.id},
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        last_comment = Comment.objects.first()
        self.assertEqual(last_comment.author, self.user)
        self.assertEqual(last_comment.text, text)
        self.assertEqual(last_comment.post, Post.objects.first())
        self.assertRedirects(
            response,
            post_detail_url
        )
        response = self.authorized_client.get(post_detail_url)
        self.assertEqual(response.context['comments'][0], last_comment)

    def test_comment_by_an_unauthorized_user(self):
        """Проверь, что аноним не может оставлять комментарии."""

        login_url = reverse('users:login')
        url = reverse('posts:add_comment', args=(self.post.id,))
        comment_count = Comment.objects.count()
        response = self.client.post(
            url,
            data={
                'text': 'Люблю оставлять анонимные комменты',
                'post': self.post.id
            },
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_post_creation_with_non_image_file(self):
        """Проверяет, что форма выдаст ошибку при создании поста
        с файлом, не являющимся изображением."""

        fake = Faker('ru_RU')
        post_count = Post.objects.count()
        file_content = fake.binary(length=64)
        uploaded = SimpleUploadedFile(
            name=fake.file_name(extension='avi'),
            content=file_content,
            content_type='video'
        )
        form_data = {
            'text': fake.text(),
            'image': uploaded,
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFormError(
            response,
            'form',
            'image',
            ('Загрузите правильное изображение. Файл, который вы загрузили, '
             'поврежден или не является изображением.')
        )
