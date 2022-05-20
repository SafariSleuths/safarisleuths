from flask import Flask
from api_response import ApiErrorResponse

app = Flask(__name__, static_url_path='', static_folder='ui/build')


@app.route('/api/v1/predict_counts', methods=['POST'])
def predict_counts_handler():
    return ApiErrorResponse(status="ok", error='not implemented'), 501


@app.route('/api/v1/teach_counts', methods=['POST'])
def teach_counts_handler():
    return ApiErrorResponse(status="error", error='not implemented'), 501


@app.route('/api/v1/debug_counts', methods=['POST'])
def debug_counts_handler():
    return ApiErrorResponse(status="error", error='not implemented'), 501


if __name__ == "__main__":
    app.run()
