from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_404_returns_correct_template(self):
        """404 ошибка возвращает правильный кастомный шаблон
        и ответ сервера."""

        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
