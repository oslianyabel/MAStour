from django.http import HttpRequest

from tours.models import SocialLink


def social_links(request: HttpRequest) -> dict:
    """Expose active social network links to every template (footer)."""
    return {'social_links': SocialLink.objects.filter(is_active=True)}
