from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('free', '자유'),
                    ('race_review', '대회 후기'),
                    ('injury', '부상/재활'),
                    ('gear', '장비 추천'),
                    ('training', '훈련 팁'),
                    ('question', '질문'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
