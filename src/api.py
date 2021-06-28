import copy
from flask import Flask, request, jsonify


from rohit import worker
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


@app.route('/bestRules', methods=['POST'])
def bestRules():
    data = request.json
    # print(data['options']["hall"][1]["p2"]["value"])
    # print(data['options'],data['output'] )
    bestRules = main(data['options'], False, data['output'])
    return jsonify(bestRules)

def main(option = None, test = None, vehicle = None):
    config0 = option
    output_dict = {}
    for idx, run in enumerate(["optimize", "monitor", "safety"]):
        config = copy.deepcopy(config0)
        config["hall"][1]["p2"]["value"] = idx+1
        result_dict = worker(config, test, vehicle)

        output_dict.update({run: result_dict})
    return output_dict

if __name__ == '__main__':
    app.run(debug=True)
