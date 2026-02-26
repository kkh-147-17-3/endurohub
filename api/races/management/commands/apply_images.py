from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'AI 검토 후 선별된 이미지를 DB에 반영'

    def add_arguments(self, parser):
        parser.add_argument(
            'race_id', type=int,
            help='대회 ID',
        )
        parser.add_argument(
            '--main', type=str, default=None,
            help='대표 이미지 URL',
        )
        parser.add_argument(
            '--course', nargs='*', default=[],
            help='코스 이미지 URL (여러 개 가능)',
        )
        parser.add_argument(
            '--giveaway', nargs='*', default=[],
            help='사은품 이미지 URL (여러 개 가능)',
        )
        parser.add_argument(
            '--from-review', action='store_true',
            help='review 파일에서 자동 로드',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='실제 저장하지 않고 미리보기만',
        )

    def handle(self, *args, **options):
        from races.models import Race

        race_id = options['race_id']
        try:
            race = Race.objects.get(id=race_id)
        except Race.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'대회를 찾을 수 없습니다: {race_id}'))
            return

        self.stdout.write(f'대회: [{race.id}] {race.title}')

        main_image = options['main']
        course_images = options['course']
        giveaway_images = options['giveaway']

        if options['from_review']:
            # TODO: Load from review JSON file
            self.stdout.write(self.style.WARNING(
                'Review 파일 로드는 아직 구현되지 않았습니다.'
            ))

        if not main_image and not course_images and not giveaway_images:
            self.stdout.write(self.style.WARNING('적용할 이미지가 없습니다.'))
            self.stdout.write('사용법:')
            self.stdout.write('  --main="URL" : 대표 이미지')
            self.stdout.write('  --course URL1 URL2 : 코스 이미지')
            self.stdout.write('  --giveaway URL : 사은품 이미지')
            self.stdout.write('  --from-review : review 파일에서 로드')
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('--dry-run 모드: 실제 저장하지 않음'))
            return

        update_data = {}
        if main_image:
            update_data['image_url'] = main_image
        if course_images:
            update_data['course_images'] = course_images
        if giveaway_images:
            update_data['giveaway_images'] = giveaway_images

        Race.objects.filter(pk=race.pk).update(**update_data)
        self.stdout.write(self.style.SUCCESS('DB 저장 완료!'))
