from django.db import models
from django.contrib.auth import get_user_model

from django.conf import settings

User = get_user_model()


class Group(models.Model):

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'


class Post(models.Model):
    text = models.TextField('Post text', help_text='Enter post text')
    pub_date = models.DateTimeField(
        'Publication date', auto_now_add=True, db_index=True
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Group',
        help_text='Group for the post',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Author',
    )
    image = models.ImageField('Image', upload_to='posts/', blank=True)

    def __str__(self):
        return self.text[: settings.TEXT_LIMIT_FOR_STR]

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Comments',
    )
    text = models.TextField(
        'Comment text', help_text='Leave your comment here'
    )
    created = models.DateTimeField(
        'Comment publication date', auto_now_add=True
    )

    def __str__(self):
        return self.text[: settings.TEXT_LIMIT_FOR_STR]

    class Meta:
        ordering = ['-created']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Blog author',
    )

    def __str__(self):
        return f'{self.user} subscription on {self.author}'

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'], name='Unique subscription'
            ),
        ]
