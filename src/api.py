import copy
import os

from flask import Flask, request, jsonify

from rohit import main
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

basePath = os.path.join( os.path.dirname(__file__) ,"api/testfiles/sampleData/")
@app.route('/v2/bestRules', methods=['POST'])
def bestRules():
    data = request.json

    output_dict, attribute_percentage, joint_attribute_percentage = main(data['options'], False, data['output'],
                                                                         json=True, debug=False)
    return jsonify({"outputs": output_dict, "attribute_percentage": attribute_percentage,
                    "joint_attribute_percentage": process_optimize_join(joint_attribute_percentage)})

@app.route('/v2/bestRules-debug', methods=['POST'])
def bestRules_debug():
    data = request.json

    output_dict, attribute_percentage, joint_attribute_percentage = main(data['options'], False, data['output'],
                                                                         json=True, debug=True)
    return jsonify({"outputs": output_dict, "attribute_percentage": attribute_percentage,
                    "joint_attribute_percentage": process_optimize_join(joint_attribute_percentage)})

@app.route('/v2/bestRules-sample', methods=['POST'])
def bestRules_sample():
    data = request.json
    sample = json.load(open(basePath + 'sample-output.json'))
    return jsonify(sample)


@app.route('/bestRules', methods=['POST'])
def bestRules_old():
    data = request.json
    outputs = load_example_files()
    return jsonify(outputs)


import json


def load_example_files():
    # basePath = "/Users/ttnguy35/Desktop/espy/src/api/testfiles/sampleData/"
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


if __name__ == '__main__':
    app.run(debug=True)
