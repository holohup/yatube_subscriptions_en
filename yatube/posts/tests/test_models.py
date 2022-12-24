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
            title='Test group',
            slug='test_group',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('The evidence before the court is incontroversable, '
                  'There is no need for the jury to retire.'
                  )
        )

    def test_models_have_correct_object_names(self):
        """Models return expected str."""

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
        """Correct, readable field titles."""

        field_verboses = {
            'text': 'Post text',
            'pub_date': 'Publication date',
            'group': 'Group',
            'author': 'Author',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """Human-readable help texts."""

        field_verboses = {
            'text': 'Enter post text',
            'group': 'Group for the post',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
