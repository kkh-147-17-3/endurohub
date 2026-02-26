from django import forms

from .models import Race


class RaceAdminForm(forms.ModelForm):
    image_file = forms.ImageField(
        required=False,
        label='대표 이미지 업로드',
        help_text='업로드하면 기존 image_path를 덮어씁니다.',
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
    )
    course_image_files = forms.FileField(
        required=False,
        label='코스 이미지 추가',
        help_text='여러 파일 선택 가능. 기존 이미지 뒤에 추가됩니다.',
        widget=forms.FileInput(attrs={'multiple': True, 'accept': 'image/*'}),
    )
    giveaway_image_files = forms.FileField(
        required=False,
        label='기념품 이미지 추가',
        help_text='여러 파일 선택 가능. 기존 이미지 뒤에 추가됩니다.',
        widget=forms.FileInput(attrs={'multiple': True, 'accept': 'image/*'}),
    )

    class Meta:
        model = Race
        exclude = [
            'course_images', 'course_image_uploads',
            'giveaway_images', 'giveaway_image_uploads',
        ]
