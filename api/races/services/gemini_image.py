import base64
import logging
import re
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SEASON_THEMES = {
    1: 'crisp winter morning, frost on ground, breath visible in cold air',
    2: 'late winter, early signs of spring, melting snow',
    3: 'early spring, cherry blossoms starting to bloom, fresh green',
    4: 'spring in full bloom, cherry blossom petals floating, warm sunlight',
    5: 'late spring, lush green landscape, clear blue sky',
    6: 'early summer, humid atmosphere, green mountains in background',
    7: 'peak summer, intense sunlight, heat shimmer on road',
    8: 'hot summer, golden hour light, dramatic clouds',
    9: 'early autumn, first hints of fall colors, cool breeze',
    10: 'mid autumn, vibrant fall foliage, golden and red leaves',
    11: 'late autumn, bare trees, fallen leaves on path',
    12: 'winter, cold blue atmosphere, distant snow-capped mountains',
}

SPORT_SCENES = {
    'running': 'marathon runners as distant silhouettes on a scenic city or riverside path, running shoes hitting pavement',
    'trail_running': 'trail runners as small silhouettes on a mountain trail, rugged terrain, forest path',
    'cycling': 'cyclists as distant silhouettes on a winding mountain road, road bikes, scenic overlook',
    'swimming': 'open water swimmers as tiny silhouettes in calm sea or lake, sunrise over water',
    'triathlon': 'triathlon transition area at dawn, bikes racked, water and road visible in distance',
}


class GeminiImageService:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = getattr(settings, 'GEMINI_IMAGE_MODEL', 'gemini-2.0-flash-exp-image-generation')

    def generate_blog_image(self, year, month, sports, image_type='monthly'):
        """Generate 16:9 featured blog image."""
        return self._generate(year, month, sports, image_type, '16:9', 'featured')

    def generate_instagram_image(self, year, month, sports, image_type='monthly'):
        """Generate 1:1 square Instagram image."""
        return self._generate(year, month, sports, image_type, '1:1', 'instagram')

    def _generate(self, year, month, sports, image_type, aspect, suffix):
        if not self.api_key:
            logger.warning('GEMINI_API_KEY not configured')
            return None

        prompt = self._build_prompt(month, sports, aspect)
        image_data = self._call_api(prompt)
        if not image_data:
            return None

        prefix = '접수중_' if image_type == 'open' else ''
        filename = f'{year}년_{month}월_{prefix}대회일정_{suffix}.png'
        return self._save_image(image_data, filename)

    def _build_prompt(self, month, sports, aspect):
        season = SEASON_THEMES.get(month, 'neutral atmosphere')
        sport_list = [SPORT_SCENES.get(s, '') for s in sports if s in SPORT_SCENES]
        sport_desc = '; '.join(sport_list[:2]) if sport_list else SPORT_SCENES['running']

        return (
            f'Cinematic {aspect} landscape photograph. {season}. '
            f'{sport_desc}. '
            f'Atmospheric depth, volumetric light rays, soft bokeh background. '
            f'Professional sports photography style, dramatic composition. '
            f'NO text, NO logos, NO watermarks, NO overlays. '
            f'People shown ONLY as distant silhouettes. '
            f'Muted, desaturated color palette with one warm accent color.'
        )

    def _call_api(self, prompt):
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent'
        headers = {'Content-Type': 'application/json'}
        params = {'key': self.api_key}
        body = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']},
        }

        try:
            resp = requests.post(url, json=body, headers=headers, params=params, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            for candidate in data.get('candidates', []):
                for part in candidate.get('content', {}).get('parts', []):
                    if 'inlineData' in part:
                        return part['inlineData']['data']
        except Exception as e:
            logger.error('Gemini API error', extra={'error': str(e)})
        return None

    def _save_image(self, base64_data, filename):
        output_dir = Path(settings.BASE_DIR) / 'storage' / 'blog-posts'
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        path.write_bytes(base64.b64decode(base64_data))
        logger.info('Image saved', extra={'path': str(path), 'filename': filename})
        return str(path)
