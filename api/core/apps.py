from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Fix: psycopg2 auto-decodes json columns to Python objects,
        # but Django's JSONField.from_db_value() tries json.loads() again.
        # Patch to skip decoding when the value is already a Python object.
        from django.db.models.fields.json import JSONField

        _original_from_db_value = JSONField.from_db_value

        def _safe_from_db_value(self, value, expression, connection):
            if value is None:
                return value
            if isinstance(value, (dict, list)):
                return value
            return _original_from_db_value(self, value, expression, connection)

        JSONField.from_db_value = _safe_from_db_value
