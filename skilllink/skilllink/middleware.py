import zoneinfo
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.COOKIES.get("django_timezone")
        if tzname:
            # Clean quotes if present
            tzname = tzname.strip('"').strip("'")
            try:
                # Try zoneinfo (Python 3.9+)
                import zoneinfo
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            except Exception:
                try:
                    # Fallback to pytz
                    import pytz
                    timezone.activate(pytz.timezone(tzname))
                except Exception:
                    timezone.deactivate()
        else:
            timezone.deactivate()
        
        return self.get_response(request)
