from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        logger.info(f"Request path: {request.path} - View: {view_func.__module__}.{view_func.__name__}")
        print(f"Request path: {request.path} - View: {view_func.__module__}.{view_func.__name__}")
        # Log CORS headers for debugging
        logger.info(f"CORS Origin: {request.headers.get('Origin')}")
        logger.info(f"CORS Method: {request.method}")
        logger.info(f"CORS Headers: {request.headers}")
        return None

    def process_response(self, request, response):
        logger.info(f"Response status: {response.status_code} for path: {request.path}")
        return response
