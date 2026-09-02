from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin

from .models import CampaignEntry, CampaignWinner, GiftCoupon, RewardCampaign
from .services import draw_campaign
from .tasks import send_reward_email_task


@admin.register(RewardCampaign)
class RewardCampaignAdmin(ModelAdmin):
    list_display = [
        'name', 'status', 'starts_at', 'ends_at', 'winners_count',
        'entry_count', 'winner_count', 'drawn_at',
    ]
    list_filter = ['status', 'starts_at', 'ends_at']
    search_fields = ['name', 'prize_name']
    ordering = ['-starts_at']
    readonly_fields = [
        'candidate_count', 'candidate_hash', 'draw_seed', 'drawn_at',
        'created_at', 'updated_at',
    ]
    actions = ['draw_selected_campaigns']

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if obj and obj.status in {
            RewardCampaign.STATUS_DRAWN,
            RewardCampaign.STATUS_COMPLETED,
        }:
            fields.extend([
                'name', 'prize_name', 'starts_at', 'ends_at',
                'winners_count', 'status',
            ])
        return fields

    @admin.display(description='응모자')
    def entry_count(self, obj):
        return obj.entries.count()

    @admin.display(description='당첨자')
    def winner_count(self, obj):
        return obj.winners.count()

    @admin.action(description='선택한 캠페인 추첨 및 이메일 발송')
    def draw_selected_campaigns(self, request, queryset):
        completed = 0
        for campaign in queryset:
            try:
                winner_ids = draw_campaign(campaign.pk)
            except ValidationError as exc:
                self.message_user(
                    request,
                    f'{campaign.name}: {"; ".join(exc.messages)}',
                    level=messages.ERROR,
                )
                continue
            completed += 1
            self.message_user(
                request,
                f'{campaign.name}: {len(winner_ids)}명 추첨을 완료했고 이메일 발송을 예약했습니다.',
                level=messages.SUCCESS,
            )
        if completed == 0:
            self.message_user(request, '추첨된 캠페인이 없습니다.', level=messages.WARNING)


@admin.register(GiftCoupon)
class GiftCouponAdmin(ModelAdmin):
    list_display = ['campaign', 'masked_code_display', 'has_image', 'expires_on', 'status', 'winner_email']
    list_filter = ['campaign', 'status', 'expires_on']
    search_fields = ['campaign__name', 'winner__email']
    ordering = ['campaign', 'id']
    readonly_fields = ['status', 'winner', 'created_at', 'updated_at']

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if obj and obj.status != GiftCoupon.STATUS_AVAILABLE:
            fields.extend(['campaign', 'code', 'redemption_url', 'image', 'expires_on'])
        return fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != GiftCoupon.STATUS_AVAILABLE:
            return False
        return super().has_delete_permission(request, obj)

    @admin.display(description='쿠폰 코드')
    def masked_code_display(self, obj):
        return obj.masked_code

    @admin.display(description='이미지', boolean=True)
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(description='당첨 이메일')
    def winner_email(self, obj):
        return obj.winner.email if obj.winner_id else '-'


@admin.register(CampaignEntry)
class CampaignEntryAdmin(ModelAdmin):
    list_display = ['campaign', 'user', 'review', 'created_at']
    list_filter = ['campaign', 'created_at']
    search_fields = ['campaign__name', 'user__email', 'review__comment']
    ordering = ['-created_at']
    readonly_fields = ['campaign', 'user', 'review', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CampaignWinner)
class CampaignWinnerAdmin(ModelAdmin):
    list_display = ['campaign', 'email', 'status', 'email_attempts', 'email_sent_at', 'created_at']
    list_filter = ['campaign', 'status', 'created_at']
    search_fields = ['campaign__name', 'email']
    ordering = ['-created_at']
    readonly_fields = [
        'campaign', 'entry', 'user', 'email', 'status', 'email_attempts',
        'delivery_started_at', 'email_sent_at', 'last_error', 'created_at', 'updated_at',
    ]
    actions = ['retry_email_delivery']

    @admin.action(description='선택한 당첨 메일 다시 발송')
    def retry_email_delivery(self, request, queryset):
        queued = 0
        for winner in queryset.exclude(status=CampaignWinner.STATUS_SENT):
            send_reward_email_task.delay(winner.pk)
            queued += 1
        self.message_user(request, f'{queued}건의 이메일 발송을 예약했습니다.')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
