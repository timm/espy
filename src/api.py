import copy
from flask import Flask, request, jsonify


from rohit import main
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


@app.route('/bestRules', methods=['POST'])
def bestRules():
    data = request.json
    # print(data['options']["hall"][1]["p2"]["value"])
    # print(data['options'],data['output'] )
    bestRules = main(data['options'], False, data['output'], json=True)
    return jsonify(bestRules)


# def main(option=None, test=None, vehicle=None):
#     # define vehicle type (taxi, package, scout)
#     print("Recommended: ", vehicle)
#
#     # read configuration
#     config0 = read_config(option)
#     output_dict = {}
#
#     # record original bounding for each attribute
#     if vehicle == "taxi":
#         temp_idx = 0
#     else:
#         temp_idx = 1
#
#     bound = {}
#     for idx, item in enumerate(config0["variables"][temp_idx]["v" + str(temp_idx + 1)]["ranges"]):
#         name = item["x" + str(idx + 1)]["name"]
#         min_val = item["x" + str(idx + 1)]["min_value"]
#         max_val = item["x" + str(idx + 1)]["max_value"]
#
#         bound.update({name: (min_val, max_val)})
#
#     for idx, run in enumerate(["optimize", "monitor", "safety"]):
#         config = copy.deepcopy(config0)
#         print("")
#         print("Recommended for", run)
#         config["hall"][1]["p2"]["value"] = idx + 1
#         result_dict = worker(config, test, vehicle, run, bound)
#
#         output_dict.update({run: result_dict})
#
#     return output_dict

# def main(option = None, test = None, vehicle = None):
#     config0 = option
#     output_dict = {}
#     for idx, run in enumerate(["optimize", "monitor", "safety"]):
#         config = copy.deepcopy(config0)
#         config["hall"][1]["p2"]["value"] = idx+1
#         result_dict = worker(config, test, vehicle)
#
#         output_dict.update({run: result_dict})
#     return output_dict

if __name__ == '__main__':
    app.run(debug=True)
