from flask_cors import CORS
from api import create_app

app = create_app()

if __name__ == "__main__":
    CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["X-Total-Count"],
         supports_credentials=True)
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=('cert.pem', 'key.pem'))
