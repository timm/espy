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
    # bestRules = main(data['options'], False, data['output'], json=True)
    bestRules = {}
    outputs = load_example_files()
    return jsonify(outputs)


import json


def load_example_files():
    basePath = "/Users/ttnguy35/Desktop/espy/src/api/testfiles/sampleData/"

    monitor_joint = json.load(open(basePath + 'monitor_joint.json'))
    monitor_single = json.load(open(basePath + 'monitor_single.json'))
    optimize_joint = process_optimize_join(json.load(open(basePath + 'optimize_joint.json')))
    optimize_single = json.load(open(basePath + 'optimize_single.json'))
    safety_joint = json.load(open(basePath + 'safety_joint.json'))
    safety_single = json.load(open(basePath + 'safety_single.json'))
    bestRules = json.load(open(basePath + 'output-fromZhao.json'))

    return {"monitor_joint": monitor_joint, "monitor_single": monitor_single, "optimize_joint": optimize_joint,
            "optimize_single": optimize_single, "safety_joint": safety_joint, "safety_single": safety_single,
            "bestRules": bestRules}


def process_optimize_join(monitor_joint):
    data = monitor_joint

    newData = {}

    # Re-arrange numbers for each entry
    for key in data.keys():
        newDataSub = {}
        # print(data[key])

        # Full dictionary for the data entry pairs
        nodeDict = {}
        for key2 in data[key].keys():
            # Turn X and Values into a x & y pair
            values = key2.split(", ")
            node = {}
            node['x'] = int(values[0])
            node['y'] = data[key][key2]

            # Sort the nodes by Y rows
            if values[1] not in nodeDict:
                nodeDict[values[1]] = []
            nodeDict[values[1]].append(node)
            # print(values[1])
            # print(node)

        # print("nodeDict")
        # print(nodeDict)

        # Apply to Pair
        # if key not in newData: newData[key] = []
        attributes = key.split(", ")
        newDataSub[attributes[1]] = nodeDict

        if attributes[0] not in newData:
            newData[attributes[0]] = []
        newData[attributes[0]].append(newDataSub)

    return newData


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
