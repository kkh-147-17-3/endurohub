"""Resolve public race URLs, including aliases retained after a merge."""

from .models import Race, RaceAlias


def resolve_race(identifier: str) -> Race:
    """Return the final canonical race or raise ``Race.DoesNotExist``.

    Live identifiers take precedence. A merge repoints all earlier aliases in
    the same transaction, so A -> B -> C never requires a redirect chain.
    """
    if identifier.isascii() and identifier.isdigit():
        numeric_id = int(identifier)
        race = Race.objects.filter(pk=numeric_id).first() if numeric_id <= 2**63 - 1 else None
    else:
        race = Race.objects.filter(slug=identifier).first()
    if race is not None:
        return race
    alias = RaceAlias.objects.select_related('race').filter(alias=identifier).first()
    if alias is None:
        raise Race.DoesNotExist
    return alias.race
