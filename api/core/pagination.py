from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LaravelStylePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = None

    def get_first_link(self) -> str | None:
        assert self.page is not None
        assert self.request is not None
        if not self.page.paginator.count:
            return None
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, 1)

    def get_last_link(self) -> str | None:
        assert self.page is not None
        assert self.request is not None
        if not self.page.paginator.count:
            return None
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, self.page.paginator.num_pages)

    @staticmethod
    def replace_query_param(url: str, key: str, val: int | str) -> str:
        from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query[key] = [str(val)]
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def get_paginated_response(self, data: Any) -> Response:
        assert self.page is not None
        return Response({
            'data': data,
            'meta': {
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
                'perPage': self.page_size,
                'total': self.page.paginator.count,
                'from': self.page.start_index(),
                'to': self.page.end_index(),
            },
            'links': {
                'first': self.get_first_link(),
                'last': self.get_last_link(),
                'prev': self.get_previous_link(),
                'next': self.get_next_link(),
            }
        })

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'data': schema,
                'meta': {
                    'type': 'object',
                    'properties': {
                        'currentPage': {'type': 'integer'},
                        'lastPage': {'type': 'integer'},
                        'perPage': {'type': 'integer'},
                        'total': {'type': 'integer'},
                        'from': {'type': 'integer'},
                        'to': {'type': 'integer'},
                    }
                },
                'links': {
                    'type': 'object',
                    'properties': {
                        'first': {'type': 'string', 'nullable': True},
                        'last': {'type': 'string', 'nullable': True},
                        'prev': {'type': 'string', 'nullable': True},
                        'next': {'type': 'string', 'nullable': True},
                    }
                },
            }
        }
