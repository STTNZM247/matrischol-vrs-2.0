from django.utils.deprecation import MiddlewareMixin


class NoCacheForAuthPagesMiddleware(MiddlewareMixin):
    """Prevent browser caching for pages that require login.

    This middleware sets headers to avoid cached pages allowing access after logout.
    It applies these headers to any request under '/accounts/' and to responses
    that contain 'registro_id' in the session.
    """

    def process_response(self, request, response):
        try:
            path = request.path or ''
            # apply to accounts paths or when a session key for our auth exists
            if path.startswith('/accounts/') or request.session.get('registro_id'):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
        except Exception:
            pass
        return response
