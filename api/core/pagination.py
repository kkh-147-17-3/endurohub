from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Django/DRF 스타일 페이지 번호 페이지네이션.

    응답은 DRF 기본 봉투인 {"count", "next", "previous", "results"}를 사용한다.
    page_size 쿼리 파라미터는 받지 않고, 뷰에서 per_page 쿼리 파라미터로
    page_size를 직접 덮어쓰는 방식(상한 100)으로만 페이지 크기를 조절한다.
    """

    page_size = 20
    page_size_query_param = None
