from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import models


class Post(models.Model):
    nickname = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=100)
    content = models.TextField()
    images = models.JSONField(null=True, blank=True)
    password = models.CharField(max_length=255)
    ip_hash = models.CharField(max_length=64)
    view_count = models.PositiveIntegerField(default=0)
    races = models.ManyToManyField(
        'races.Race',
        through='PostRace',
        related_name='posts',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'posts'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def display_nickname(self):
        return self.nickname or '익명'

    @property
    def image_srcs(self):
        if not self.images or not isinstance(self.images, list):
            return []
        return [f'{settings.STORAGE_URL}{path}' for path in self.images]

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def like_count(self):
        return self.likes.count()

    def check_password(self, raw_password):
        """Verify password against bcrypt hash (PHP compatible)."""
        return check_password(raw_password, self.password)

    def increment_view_count(self):
        Post.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )


class PostRace(models.Model):
    """Pivot table for Post <-> Race many-to-many."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    race = models.ForeignKey('races.Race', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'post_race'
        unique_together = [('post', 'race')]


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    nickname = models.CharField(max_length=50, null=True, blank=True)
    content = models.TextField()
    password = models.CharField(max_length=255)
    ip_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'post_comments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.display_nickname}: {self.content[:30]}'

    @property
    def display_nickname(self):
        return self.nickname or '익명'

    @property
    def is_reply(self):
        return self.parent_id is not None

    def check_password(self, raw_password):
        """Verify password against bcrypt hash (PHP compatible)."""
        return check_password(raw_password, self.password)


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    ip_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'post_likes'
        unique_together = [('post', 'ip_hash')]

    def __str__(self):
        return f'Like on Post#{self.post_id} by {self.ip_hash[:8]}...'
