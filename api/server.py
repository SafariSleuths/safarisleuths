from flask import Flask

from api_response import ApiResponse, Status

app = Flask(__name__, static_url_path='', static_folder='ui/build')


@app.route('/api/v1/predict_counts', methods=['POST'])
def predict_counts_handler():
    return ApiResponse(status=Status.OK, photo_metrics=[
        {
            'file': '/data/zebra-1-annotated.jpeg',
            'predictions': [{'animal': 'zebra', 'count': 1}]
        },
        {
            'file': '/data/zebra-2-annotated.jpeg',
            'predictions': [{'animal': 'zebra', 'count': 1}]
        },
        {
            'file': '/data/zebra-3-annotated.jpeg',
            'predictions': [{'animal': 'zebra', 'count': 3}]
        },
    ]).to_dict()


@app.route('/api/v1/teach_counts', methods=['POST'])
def teach_counts_handler():
    return ApiResponse(status=Status.ERROR, error='not implemented').to_dict(), 501


@app.route('/api/v1/debug_counts', methods=['POST'])
def debug_counts_handler():
    return ApiResponse(status=Status.ERROR, error='not implemented').to_dict(), 501


if __name__ == "__main__":
    app.run()
