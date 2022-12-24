from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Вокруг качается ковыль, за далью - даль, за былью - быль, '
                  'И небольшой автомобиль вздымает в поле пыль.'
                  )
        )

    def test_models_have_correct_object_names(self):
        """Модели возвращают ожидаемые str."""

        expected_group_name = self.group.title
        expected_post_name = self.post.text[:settings.TEXT_LIMIT_FOR_STR]
        expected_str = {
            expected_group_name: str(self.group),
            expected_post_name: str(self.post),
        }
        for expectation, string in expected_str.items():
            with self.subTest(expectation=expectation):
                self.assertEqual(expectation, string)

    def test_verbose_name(self):
        """Правильные, читабельные названия полей."""

        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """Хелпы человекопонятны."""

        field_verboses = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
