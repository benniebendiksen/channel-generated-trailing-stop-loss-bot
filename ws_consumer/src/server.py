import json

from flask import Flask, render_template, request, jsonify
import simple_websocket
from flask_restful import Api, Resource, reqparse
# from receiver import BinanceWebsocketConsumer

app = Flask(__name__)
api = Api(app)


@app.route('/echo', websocket=True)
# def echo():
#     print("Device connected ...")
#     obj = BinanceWebsocketConsumer()
#     ws = simple_websocket.Server(request.environ)
#     try:
#         while True:
#             message = next(obj.process_stream_data_from_trade_stream_buffer())
#             ws.send(json.dumps(message))
#     except (KeyboardInterrupt, EOFError, simple_websocket.ConnectionClosed):
#         obj.stop()

#     print("Device disconnected ...")
#     return ""


@app.route('/')
def index():
    return "Hello World!"


class BinanceApi(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('method', type=str, location='json', required=True)
        self.reqparse.add_argument('params', type=dict, location='json')
        super(BinanceApi, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        method = args['method']
        params = args['params']

        obj = BinanceManager()
        attr = getattr(obj, method)
        # checks if attribute is callable
        if callable(attr):
            return attr(**params), 201
        else:
            # raise error
            raise Exception("Method not found")


api.add_resource(BinanceApi, '/api/', endpoint='api')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5054)
