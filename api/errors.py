# api/errors.py

from flask import jsonify

class BaseAPIException(Exception):
    """Base class for all custom API exceptions."""
    status_code: int = 400

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> dict:
        return {"error": self.message}


class BadRequestError(BaseAPIException):
    status_code = 400


class UnauthorizedError(BaseAPIException):
    status_code = 401


class ForbiddenError(BaseAPIException):
    status_code = 403


class NotFoundError(BaseAPIException):
    status_code = 404


class ConflictError(BaseAPIException):
    status_code = 409


class InternalServerError(BaseAPIException):
    status_code = 500


def register_error_handlers(app):
    """
    Attach custom error handlers to the Flask application.
    Called once inside the application factory or main app setup.
    """
    @app.errorhandler(BaseAPIException)
    def handle_api_exceptions(e: BaseAPIException):
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        return response
    @app.errorhandler(404)
    def handle_404(e):
        response = jsonify({"error": "The requested resource was not found."})
        response.status_code = 404
        return response
    @app.errorhandler(Exception)
    def handle_unexpected_exceptions(e: Exception):
        """
        Catch-all for any uncaught exceptions.
        Logs can go here if needed.
        """
        response = jsonify({"error": "An unexpected error occurred."})
        response.status_code = 500
        return response
