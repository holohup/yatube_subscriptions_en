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
            title='Test group',
            slug='test_group',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='An old dog has been guarding flowers',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_creation_by_an_authorized_user(self):
        """When an authorized user fills a valid form, a post is created."""

        fake = Faker('en_US')
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
        """Post author can edit it."""

        test_post = Post.objects.create(
            author=self.user,
            text='And whispered to her: "there is always place for hope"',
            group=self.group
        )
        new_group = Group.objects.create(
            title='Group for editing',
            slug='test_edit_group',
            description='If the post can be edited, it will go here',
        )
        post_count = Post.objects.count()
        text = 'Warm wind cuddled with his hair'
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
        """An authorized user cannot edit other user's post."""

        text = 'A quick brown fox jumps over the edge, flies and dissapears'
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
        """Attempt to create a post by an unauthorized user."""

        login_url = reverse('users:login')
        url = reverse('posts:post_create')
        post_count = Post.objects.count()
        response = self.client.post(
            url,
            data={
                'text': 'We have got to go ASAP!', 'group': self.group.id
            },
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_comment_by_an_authorized_user(self):
        """Check if an authorized user can leave a comment,
        And if upon commenting the comment appears on the post page.
        """

        text = 'Who would have thouth! Splendid!'
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
        """Anonymous can't leave a comment."""

        login_url = reverse('users:login')
        url = reverse('posts:add_comment', args=(self.post.id,))
        comment_count = Comment.objects.count()
        response = self.client.post(
            url,
            data={
                'text': 'I love anonymous trolling',
                'post': self.post.id
            },
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_post_creation_with_non_image_file(self):
        """Check if the form returns an error upon being
        submitted with a file which is not an image."""

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
            ('Upload a valid image. The file you uploaded was either not an '
             'image or a corrupted image.')
        )
