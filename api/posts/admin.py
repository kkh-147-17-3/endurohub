from django.contrib import admin
from core.utils import post_count_subqueries
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Post, PostComment, PostLike, PostRace


class PostRaceInline(TabularInline):
    model = PostRace
    extra = 1
    autocomplete_fields = ['race']


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = [
        'id', 'title_short', 'display_nickname_col', 'view_count',
        'comments_count_col', 'likes_count_col', 'tagged_races_col', 'created_at',
    ]
    list_filter = ['created_at']
    search_fields = ['title', 'nickname', 'content']
    ordering = ['-created_at']
    readonly_fields = [
        'ip_hash', 'view_count', 'created_at', 'updated_at',
        'images_preview', 'comments_count_display', 'likes_count_display',
    ]
    inlines = [PostRaceInline]

    fieldsets = (
        ('게시글 정보', {
            'fields': ('title', 'nickname', 'content'),
        }),
        ('이미지', {
            'fields': ('images_preview',),
        }),
        ('메타 정보', {
            'fields': (
                'view_count', 'comments_count_display', 'likes_count_display',
                'created_at', 'updated_at',
            ),
        }),
    )

    def get_queryset(self, request):
        comment_count_sq, like_count_sq = post_count_subqueries()
        return super().get_queryset(request).annotate(
            _comments_count=comment_count_sq,
            _likes_count=like_count_sq,
        )

    @admin.display(description='제목')
    def title_short(self, obj):
        return obj.title[:30] + ('...' if len(obj.title) > 30 else '')

    @admin.display(description='닉네임')
    def display_nickname_col(self, obj):
        return obj.display_nickname

    @admin.display(description='댓글', ordering='_comments_count')
    def comments_count_col(self, obj):
        return getattr(obj, '_comments_count', 0)

    @admin.display(description='좋아요', ordering='_likes_count')
    def likes_count_col(self, obj):
        return getattr(obj, '_likes_count', 0)

    @admin.display(description='태그된 대회')
    def tagged_races_col(self, obj):
        races = obj.races.all()[:3]
        if not races:
            return '-'
        badges = []
        for race in races:
            badges.append(format_html(
                '<span style="padding:1px 6px; border-radius:4px; '
                'font-size:11px; border:1px solid #d1d5db; '
                'margin-right:2px;">{}</span>',
                race.title[:20],
            ))
        return format_html(''.join(str(b) for b in badges))

    @admin.display(description='첨부 이미지')
    def images_preview(self, obj):
        if not obj.images or not isinstance(obj.images, list):
            return '이미지 없음'
        from django.conf import settings
        html_parts = ['<div style="display:flex; flex-wrap:wrap; gap:8px;">']
        for image in obj.images:
            url = f'{settings.STORAGE_URL}{image}'
            html_parts.append(
                f'<a href="{url}" target="_blank">'
                f'<img src="{url}" style="width:96px; height:96px; '
                f'object-fit:cover; border-radius:4px; border:1px solid #e5e7eb;">'
                f'</a>'
            )
        html_parts.append('</div>')
        return format_html(''.join(html_parts))

    @admin.display(description='댓글 수')
    def comments_count_display(self, obj):
        return obj.comments.count()

    @admin.display(description='좋아요 수')
    def likes_count_display(self, obj):
        return obj.likes.count()


@admin.register(PostComment)
class PostCommentAdmin(ModelAdmin):
    list_display = ['id', 'post_link', 'display_nickname_col', 'content_short', 'is_reply_col', 'created_at']
    list_filter = ['created_at']
    search_fields = ['nickname', 'content']
    ordering = ['-created_at']
    readonly_fields = ['post', 'parent', 'ip_hash', 'created_at', 'updated_at']

    @admin.display(description='게시글')
    def post_link(self, obj):
        return format_html(
            '<a href="/admin/posts/post/{}/change/">{}</a>',
            obj.post_id, obj.post.title[:20],
        )

    @admin.display(description='닉네임')
    def display_nickname_col(self, obj):
        return obj.display_nickname

    @admin.display(description='내용')
    def content_short(self, obj):
        return obj.content[:40] + ('...' if len(obj.content) > 40 else '')

    @admin.display(description='대댓글', boolean=True)
    def is_reply_col(self, obj):
        return obj.is_reply


@admin.register(PostLike)
class PostLikeAdmin(ModelAdmin):
    list_display = ['id', 'post', 'ip_hash_short', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['post', 'ip_hash', 'created_at']

    @admin.display(description='IP Hash')
    def ip_hash_short(self, obj):
        return obj.ip_hash[:16] + '...'
