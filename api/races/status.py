"""Cancellation notices shared by model properties and SQL status filters.

Keep the patterns compatible with Python and PostgreSQL regular expressions.
Only an explicit notice counts; refund rules and conditional cancellation
policies must not turn a scheduled event into a cancelled one.
"""

import re

from django.db.models import Q


TITLE_CANCELLATION_PATTERN = (
    r'(^|[\[(【])\s*(대회\s*)?취소\s*[\])】]'
    r'|취소(\s*(안내|공지))?\s*$'
)
_CANCELLATION_DECLARATION = (
    r'(대회|행사|개최)(는|가|를|을)?\s*(전면\s*)?'
    r'취소(합니다|되었습니다|됐습니다|되었음을|하게\s*되었습니다|하기로\s*하였습니다)'
)
_CONDITION = (
    r'(\s시(에는|에|는)?(?=\s|[,，:])'
    r'|(우천|악천후|천재지변|기상\s*악화|미달|부족|발생|악화)시'
    r'|경우|[가-힣]+면|만약|만일|(할|될|일|했을|되었을)\s*때'
    r'|\s때(에는|에|는)?(?=\s|[,，:]))'
)
_SENTENCE_TEXT = r'[^.!?。]'
# A policy can use the same verb as an announcement: "우천 시 대회를 취소합니다".
# Reject a conditional clause before the declaration in that sentence, rather
# than rejecting an entire description that also contains a real announcement.
# A newline may wrap the condition, so only punctuation ends its scope.
DESCRIPTION_CANCELLATION_PATTERN = (
    r'(^|[.!?。])'
    rf'(?!{_SENTENCE_TEXT}*{_CONDITION}{_SENTENCE_TEXT}*{_CANCELLATION_DECLARATION})'
    rf'{_SENTENCE_TEXT}*{_CANCELLATION_DECLARATION}'
)


def has_cancellation_notice(title: str, description: str | None) -> bool:
    return bool(
        re.search(TITLE_CANCELLATION_PATTERN, title, re.IGNORECASE)
        or re.search(DESCRIPTION_CANCELLATION_PATTERN, description or '', re.IGNORECASE)
    )


def cancellation_query() -> Q:
    return (
        Q(status='cancelled')
        | Q(title__iregex=TITLE_CANCELLATION_PATTERN)
        | Q(description__iregex=DESCRIPTION_CANCELLATION_PATTERN)
    )
