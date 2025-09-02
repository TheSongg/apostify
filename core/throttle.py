from rest_framework.throttling import SimpleRateThrottle


class UserThrottle(SimpleRateThrottle):
    scope = 'UserThrottleRate'

    def get_cache_key(self, request, view):
        return self.get_ident(request)