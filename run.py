from flask_cors import CORS
from api import create_app

app = create_app()

if __name__ == "__main__":
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.run(host="0.0.0.0", port=5000, debug=True,ssl_context=('c   ert.pem', 'key.pem'))




