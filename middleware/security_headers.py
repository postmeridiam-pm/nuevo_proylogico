from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=()'
        csp = []
        csp.append("default-src 'self' https: data:")
        csp.append("img-src 'self' data: https:")
        csp.append("script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm")
        csp.append("style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm")
        csp.append("object-src 'none'")
        csp.append("base-uri 'self'")
        csp.append("form-action 'self'")
        csp.append("frame-ancestors 'self'")
        csp.append("frame-src 'self'")
        csp.append("connect-src 'self'")
        csp.append("font-src 'self' https://cdn.jsdelivr.net")
        response['Content-Security-Policy'] = '; '.join(csp)
        response['X-Content-Type-Options'] = 'nosniff'
        return response
