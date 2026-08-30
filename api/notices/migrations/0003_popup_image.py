# 팝업 배너 내용을 이미지 한 장으로 바꾼다 — 헤드라인·메타·참여 단계·세부
# 안내를 전부 이미지가 대신한다. 코드는 게시기간과 이동 링크만 관여한다.
# 배너 데이터가 아직 없어서 기존 컬럼은 그대로 드롭한다.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0002_popup_popupstep'),
    ]

    operations = [
        migrations.DeleteModel(name='PopupStep'),
        migrations.RemoveField(model_name='popup', name='tag'),
        migrations.RemoveField(model_name='popup', name='headline'),
        migrations.RemoveField(model_name='popup', name='headline_accent'),
        migrations.RemoveField(model_name='popup', name='subtitle'),
        migrations.RemoveField(model_name='popup', name='meta_period'),
        migrations.RemoveField(model_name='popup', name='meta_winners'),
        migrations.RemoveField(model_name='popup', name='show_dday'),
        migrations.RemoveField(model_name='popup', name='prize_note'),
        migrations.RemoveField(model_name='popup', name='prize_name'),
        migrations.RemoveField(model_name='popup', name='prize_count'),
        migrations.RemoveField(model_name='popup', name='fine_period'),
        migrations.RemoveField(model_name='popup', name='fine_announce'),
        migrations.RemoveField(model_name='popup', name='fine_note'),
        migrations.RenameField(model_name='popup', old_name='prize_image', new_name='image'),
        migrations.AddField(
            model_name='popup',
            name='image_width',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='popup',
            name='image_height',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='popup',
            name='image',
            field=models.ImageField(
                height_field='image_height', width_field='image_width',
                upload_to='popups/%Y-%m/', verbose_name='팝업 이미지',
            ),
        ),
        migrations.AddField(
            model_name='popup',
            name='image_alt',
            field=models.CharField(
                blank=True, default='', max_length=120,
                help_text='이미지를 못 보는 사람(스크린리더·로딩 실패)에게 읽히는 대체 텍스트입니다.',
                verbose_name='이미지 설명',
            ),
        ),
        migrations.AlterField(
            model_name='popup',
            name='cta_label',
            field=models.CharField(
                blank=True, default='자세히 보기', max_length=40,
                help_text='비워 두면 버튼 없이 이미지만 눌러 이동합니다.',
                verbose_name='CTA 문구',
            ),
        ),
    ]
