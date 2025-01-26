from flask_jwt_extended import JWTManager

from api.models.models import RevokedToken


def setup_jwt_callbacks(jwt: JWTManager):
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """
        Callback function to check if a token has been revoked.
        """
        jti = jwt_payload['jti']
        token = RevokedToken.query.filter_by(jti=jti).first()
        return token is not None

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        """
        Custom response for revoked tokens.
        """
        return {"message": "The token has been revoked.", "error": "token_revoked"}, 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        """
        Custom response for expired tokens.
        """
        return {"message": "The token has expired.", "error": "token_expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_response(error):
        """
        Custom response for invalid tokens.
        """
        return {"message": "Invalid token.", "error": "invalid_token"}, 401

    @jwt.unauthorized_loader
    def missing_token_response(error):
        """
        Custom response for missing tokens.
        """
        return {"message": "Request does not contain an access token.", "error": "authorization_required"}, 401