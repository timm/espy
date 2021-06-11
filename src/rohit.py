import yaml
import random
import math
import sys
import hall
import random
import copy
import json

header_row = ['Ascend_angle', 'Descend_angle_1', 'Descend_angle_2', 
                  'Cruise_speed', 'Trip_distance', 'Cruise_altitude', 'Payload', 'Wind', 
                   'Direction', 'T-', 'Long_accel-', 'Lat_accel-', 'Jerk-', 'Charging?']

### fun: read configuration ###
### - input:                ###
###    - none               ###
### - output:               ###
###    - config: dict       ###
def read_config(file):
    with open(file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    return config


### fun: generate random sims data ###
### - input:                       ###
###    - config: configuration     ###
###    - n: number of sims to gen  ###
###    - test: whether run tests   ###
###    - vehicle: vehicle type     ###
### - output:                      ###
###    - sims: a list of sims      ###
def gen_sim(config, n, test, vehicle):
    sims = []
    sims_table = []
    
    if test == False:
        progress_count = 0
        # iterate n sims
        while progress_count < n:
            temp_sim = []

            # iterate through dependent variables and generate random number for each of them
            for key, item in enumerate(config):
                temp_id = "x" + str(key+1)
                temp_name = item[temp_id]['name']
                temp_min_value = item[temp_id]['min_value']
                temp_max_value = item[temp_id]['max_value']
                
                # descend angle 2 is always 3 less than descend angle 1, handle this
                if temp_name == "Descend_angle_1":
                    temp_angle_1 = random.randint(temp_min_value, temp_max_value)
                    temp_angle_2 = temp_angle_1 - 3
                    temp_sim.append(temp_angle_1)
                    temp_sim.append(temp_angle_2)
                elif temp_name == "Descend_angle_2":
                    continue
                else:
                    temp_sim.append(random.randint(temp_min_value, temp_max_value))
            
            result_sim, sim_table = goal_cal(temp_sim, test, vehicle)
            sims.append(result_sim)
            sims_table.append(sim_table)
            progress_count += 1
    else:
        test_sims = [[7,10,7,41,6323,607,1166,11,17], [3,28,25,60,26451,720,1009,16,132], [10,30,27,47,27011,599,732,19,20], [26,23,20,72,23183,574,704,10,176], [17,16,13,46,15801,931,548,0,4], 
                    [23,18,15,82,10567,200,465,29,88], [24,23,20,25,24912,504,366,15,158], [3,30,27,41,16294,935,196,29,176], [29,19,16,28,22699,436,1239,23,176], [21,21,18,102,6571,312,1380,29,23]]
        
        for item in test_sims:
            result_sim, sim_table = goal_cal(item, test, vehicle)
            sims.append(result_sim)
            sims_table.append(sim_table)
        
        print("")
        print("-----TESTING MODE-----")

        print("right outputs:")
        result_test_sims = [[7,10,7,41,6323,607,1166,11,17,1,0,0,0,0], [3,28,25,60,26451,720,1009,16,132,0,0,0,0,1], [10,30,27,47,27011,599,732,19,20,0,2,1,1,0], [26,23,20,72,23183,574,704,10,176,0,1,2,0,0], 
                            [17,16,13,46,15801,931,548,0,4,0,0,0,0,0], [23,18,15,82,10567,200,465,29,88,0,3,3,3,0], [24,23,20,25,24912,504,366,15,158,1,0,0,0,1], [3,30,27,41,16294,935,196,29,176,4,1,0,0,0],
                            [29,19,16,28,22699,436,1239,23,176,3,0,0,0,1], [21,21,18,102,6571,312,1380,29,23,0,3,3,4,0]]
        header_row = ['Ascend_angle', 'Descend_angle_1', 'Descend_angle_2', 'Cruise_speed', 'Trip_distance', 'Cruise_altitude', 'Payload', 'Wind', 'Direction', 'T-', 'Long_accel-', 'Lat_accel-', 'Jerk-', 'Charging-']
        [print(', '.join(x for x in header_row))]
        [print(', '.join([str(x) for x in lst])) for lst in result_test_sims]

    return sims, sims_table


### fun: calculate t, longitudnal_accel, lateral_accel, jerk, and energy ###
### - input:                                                             ###
###    - sim: a simulation variables                                     ###
###    - vehicle: vehicle type                                           ###
### - output:                                                            ###
###    - sim_goal: the goals of the input sim                            ###
def goal_cal(sim, test, vehicle):
    if vehicle == "taxi":
        MTOW = 5000
    if vehicle == "delivery":
        MTOW = 100
    
    hover = 58
    cruise = 12.5
    
    # pre-defined global variables
    p5z = 150
    p6z = 5

    # change mile/h to meter/s
    if not test:
        cruise_speed = round(sim[3]*0.44704, 0)
    else:
        cruise_speed = sim[3]

    # phase 1
    p1t = 3
    p1x, p1y, p1z = 0, 0, 5
    v1x, v1y, v1z = 0, 0, p1z/p1t
    p1long = p1z*2/(p1t**2)
    p1lat = p1x/p1t
    p1jerk = math.sqrt((p1lat/p1t) ** 2 + (p1long/p1t) ** 2)
    p1energy = ((MTOW+sim[6])/1000)**1.5 * hover * p1t / 3600
        
    # phase 2
    p2t = 5
    p2x, p2y, p2z = 35, 0, 5
    v2x, v2y, v2z = p2x/p2t + sim[7] * math.cos(math.radians(sim[8])), 0, 0
    p2long = 0
    p2lat = (p2x - p1x) * 2 / (p2t**2)
    p2jerk = math.sqrt(((p2lat-p1lat)/p2t)**2 + ((p2long-p1long)/p2t)**2)
    p2energy = (MTOW+sim[6]) * cruise / 1000 * p2t / 3600 * (cruise_speed/67)
        
    # phase 3
    p3z = sim[5]
    p3y = 0
    p3x = p2x + (p3z - p2z) / math.tan(math.radians(sim[0]))
    v3x = cruise_speed + sim[7] * math.cos(math.radians(sim[8]))
    v3y = 0
    p3t = (p3x - p2x) * 2 / (v3x + v2x + 1E-32)
    v3z = (p3z - p2z) / p3t
    p3long = (p3z - p2z) * 2 / (p3t**2)
    p3lat = ((v3x**2) - (v2x**2)) / (2 * (p3x - p2x))
    p3jerk = math.sqrt(((p3lat-p2lat)/p3t)**2 + ((p3long-p2long)/p3t)**2)
    p3energy = (MTOW+sim[6]) * cruise / 1000 * p3t / 3600 * (cruise_speed/67)
        
    # phase 4
    p4z = sim[5]
    p4y = 0
    p4x = sim[4] - (p4z - p5z) / math.tan(math.radians(sim[2])) - (p5z - p6z) / math.tan(math.radians(sim[1]))
    v4x = cruise_speed + sim[7] * math.cos(math.radians(sim[8]))
    v4y = 0
    v4z = 0
    p4t = (p4x - p3x) * 2 / (v4x + v3x + 1E-32)
    p4long = (p4z - p3z) * 2 / (p4t**2)
    p4lat = ((v4x**2) - (v3x**2)) / (2 * (p4x - p3x))
    p4jerk = math.sqrt(((p4lat-p3lat)/p4t)**2 + ((p4long-p3long)/p4t)**2)
    p4energy = (MTOW+sim[6]) * cruise / 1000 * p4t / 3600 * (cruise_speed/67)
            
    # phase 5
    if vehicle == "taxi":
        p5z = 150
    if vehicle == "delivery":
        p5z = 25
    
    p5y = 0
    p5x = p4x + (p4z - p5z) / math.tan(math.radians(sim[2]))
    v5x = v4x/2 + sim[7] * math.cos(math.radians(sim[8]))
    v5y = 0
    v5z = v5x * (p4z - p5z) / (p5x - p4x + 1E-32)
    p5t = (p5x - p4x) * 2 / (v5x + v4x + 1E-32)
    p5long = (p5z - p4z) * 2 / (p5t**2 + 1E-32)
    p5lat = ((v5x**2) - (v4x**2)) / (2 * (p5x - p4x + 1E-32))
    p5jerk = math.sqrt(((p5lat-p4lat)/(p5t + 1E-32))**2 + ((p5long-p4long)/(p5t + 1E-32))**2)
    p5energy = (MTOW+sim[6]) * cruise / 1000 * p5t / 3600 * (cruise_speed/67)
        
    # phase 6
    p6z = 5
    p6y = 0
    p6x = p5x + (p5z - p6z) / math.tan(math.radians(sim[1]))
    v6x = (v5x + 0) / 2
    v6y = 0
    p6t = (p6x - p5x) * 2 / (v6x + v5x + 1E-32)
    v6z = (p5z - p6z) / p6t
    p6long = (p6z - p5z) * 2 / (p6t**2)
    p6lat = ((v6x**2) - (v5x**2)) / (2 * (p6x - p5x))
    p6jerk = math.sqrt(((p6lat-p5lat)/p6t)**2 + ((p6long-p5long)/p6t)**2)
    p6energy = (MTOW+sim[6]) * cruise / 1000 * p6t / 3600 * (cruise_speed/67)
        
    # phase 7
    p7z = 0
    p7y = 0
    p7x = p6x
    v7x = 0
    v7y = 0
    p7t = 3
    v7z = (p6z - p7z) / p7t
    p7long = (p7z - p6z) * 2 / (p7t**2)
    p7lat = (p7x - p6x) / p7t
    p7jerk = math.sqrt(((p7lat-p6lat)/p7t)**2 + ((p7long-p6long)/p7t)**2)
    p7energy = ((MTOW+sim[6]) / 1000)**1.5 * hover * p7t / 3600
        
    sim_goal = [sim, [p1t, p2t, p3t, p4t, p5t, p6t, p7t], [p1long, p2long, p3long, p4long, p5long, p6long, p7long], [p1lat, p2lat, p3lat, p4lat, p5lat, p6lat, p7lat], 
                [p1jerk, p2jerk, p3jerk, p4jerk, p5jerk, p6jerk, p7jerk], [(p1energy+p2energy+p3energy+p4energy+p5energy+p6energy+p7energy)/((0.2*MTOW)*200/2200)]]
    
    sim_table = [sim, [p1x, p1y, p1z, v1x, v1y, v1z, p1t], [p2x, p2y, p2z, v2x, v2y, v2z, p2t], [p3x, p3y, p3z, v3x, v3y, v3z, p3t],  [p4x, p4y, p4z, v4x, v4y, v4z, p4t], 
                [p5x, p5y, p5z, v5x, v5y, v5z, p5t], [p6x, p6y, p6z, v6x, v6y, v6z, p6t], [p7x, p7y, p7z, v7x, v7y, v7z, p7t]]

    return sim_goal, sim_table


### fun: generate violation                                          ###
### - input:                                                         ###
###    - sims_goal: a list of sims with goals variables calculated   ###
### - output:                                                        ###
###    - sims_violation: a list of sims with violations in each goal ###
def violation(sims_goal, threshold, vehicle_type):
    sims_violation = []
    
    temp_threshold = threshold[vehicle_type-1]
    
    for row in sims_goal:
        # copy the first list, which is dependent variables
        dependent_v = row[0]
        
        # the second list - t, criteria: > 0
        t_violation = []
        for item in row[1]:
            if item > temp_threshold['y'+str(vehicle_type)]['rules'][0]['r1']['value']:
                t_violation.append(0)
            else:
                t_violation.append(1)
        
        # the third list - long_accel, criteria: phase 3-6 < 1
        long_accel_violation = []
        for i, item in enumerate(row[2]):
            if i == 2 or i == 3 or i == 4 or i == 5:
                if abs(item) > temp_threshold['y'+str(vehicle_type)]['rules'][1]['r2']['value']:
                    long_accel_violation.append(1)
                else:
                    long_accel_violation.append(0)
            else:
                long_accel_violation.append(0)
        
        # the forth list - alt_accel, criteria: phase 3-6 < 1
        lat_accel_violation = []
        for i, item in enumerate(row[3]):
            if i == 2 or i == 3 or i == 4 or i == 5:
                if abs(item) > temp_threshold['y'+str(vehicle_type)]['rules'][2]['r3']['value']:
                    lat_accel_violation.append(1)
                else:
                    lat_accel_violation.append(0)
            else:
                lat_accel_violation.append(0)
        
        # the fifth list - jerk, criteria: phase 3-6 < 0.3
        jerk_violation = []
        for i, item in enumerate(row[4]):
            if i == 2 or i == 3 or i == 4 or i == 5:
                if item > temp_threshold['y'+str(vehicle_type)]['rules'][3]['r4']['value']:
                    jerk_violation.append(1)
                else:
                    jerk_violation.append(0)
            else:
                jerk_violation.append(0)
        
        # the sixth list - charging, criteria: < 20%
        if row[5][0] > temp_threshold['y'+str(vehicle_type)]['rules'][4]['r5']['value']:
            charging_violation = [1]
        else:
            charging_violation = [0]

        sims_violation.append([dependent_v, t_violation, long_accel_violation, lat_accel_violation, jerk_violation, charging_violation])
    
    return sims_violation


### fun: generate goal table                                       ###
### - input:                                                       ###
###    - sims_violation: a list of sims with violations calculated ###
###    - choice: an integer to choose the way to generate goals    ###
### - output:                                                      ###
###    - sims_final: a list of sims with goals generated           ###
def goal_generate(sims_violation, choice):
    sims_final = []
    
    if choice == 1:
        for row in sims_violation:
            # output_line = row[0] + [1 if sum(row[1])>0 else 0, sum(row[2]), sum(row[3]), sum(row[4]), sum(row[5])]
            output_line = row[0] + [sum(row[1]), sum(row[2]), sum(row[3]), sum(row[4]), sum(row[5])]
            sims_final.append(output_line)
    elif choice == 2:
        for row in sims_violation:
            output_line = row[0] + [1 if 1 in row[1] else 0, 1 if 1 in row[2] else 0, 1 if 1 in row[3] else 0, 1 if 1 in row[4] else 0, 1 if 1 in row[5] else 0]
            sims_final.append(output_line)
    elif choice == 3:
        for row in sims_violation:
            final_count = 0
            for i in range(1, 6):
                final_count += sum(row[i])
                
            output_line = row[0] + [final_count]
            sims_final.append(output_line)
    elif choice == 4:
        for row in sims_violation:
            final_count = 0
            for i in range(1, 6):
                final_count += sum(row[i])
            
            output_line = row[0] + [1 if final_count > 0 else 0]
            sims_final.append(output_line)
    
    return sims_final

def worker(config, test, vehicle):
    if test:
        suggestions = useit(config, test, vehicle)
        showResults(suggestions)
    else:
        result_dict = {}

        random.seed(config["control"][3]['c4']["value"])
        for i in range(config["control"][1]["c2"]["value"]):
            simulationResults = useit(config, test, vehicle)
            # print("current configuration")
            # print(config['variables'])
            #showResults(simulationResults)
            if i == 0:
                recentConfig = config
            
            config, before, effect, best = updateOptions(simulationResults, config, vehicle)

            if config is None:
                return result_dict

            # output record
            result_dict.update({"r"+str(i+1): {"before": before, "effect": effect, "rule": best}})
            recentConfig = config
        
        return result_dict


class obj:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i) : return "{" + ', '.join(
      [f":{k} {v}" for k, v in sorted(i.__dict__.items()) if k[0] != "_"]) + "}"

def rounds(lst,r=1): return [round(x,r) for x in lst]

def reconstruct(config):
    updatedConfig = {}
    for idx, item in enumerate(config["hall"]):
        updatedConfig.update({item["p"+str(idx+1)]['name']: item["p"+str(idx+1)]['value']})
    
    return updatedConfig

def updateOptions(simulationResults, config, vehicle):
    t= hall.Tab([header_row] + simulationResults)
    print("LEN", len(t.rows))
    rows=t.dominates()
    #   my = obj(**config["hall"])
    my = obj(**reconstruct(config))
    my.data = "simuations"
    print("my",my)
    stop=len(rows)//my.elite
    best, rest = t.clone(rows[:stop]), t.clone(rows[stop:])
    print("all ",rounds(t.y(),    my.yround)) 
    print("best",rounds(best.y(), my.yround)) 
    print("rest",rounds(rest.y(), my.yround)) 
    print("\nSource : ",my.data)
    print("Goal   : ",("Optimize" if my.act==1 else (
                        "Monitor"  if my.act==2 else "Safety")))
    t.summary()
    rules = hall.contrast(best,rest,my)
    ranges=set()
    effect = None
    for rule in rules:
        picked = hall.selects(t, rule)
        effect = rounds( picked.y(), my.yround)

        #print(len(hall.selects(t, rule).rows))
        print("")
        print(effect, rule)
        print(hall.showRule(rule))
        for x in hall.parts(rule): ranges.add(x)
    # print(ranges)
    before = None
    if best := hall.bestTreatment(t, rules, stop, my):
        before = rounds(t.y(), my.yround)
        print("BEST", best)
        print("\nRecommended previous", before, "\tRecommended now", effect, "\tRecommended best rule: ", best)

    newConfig = updateConfig(best, config, vehicle)
    return newConfig, before, effect, best

def updateConfig(best, config, vehicle):
    if best is None:
        print("Best Recommended configuration, no more rules to suggest!")
        return None

    for rule in best:
        tempIdx = rule[1]
        tempRange = rule[2]
        
        if vehicle == "taxi":
            tempConfig = config['variables'][0]["v1"]["ranges"][tempIdx]['x'+str(tempIdx+1)]

            if tempRange[0][0] > tempConfig['min_value']:
                config['variables'][0]["v1"]["ranges"][tempIdx]['x'+str(tempIdx+1)]['min_value'] = tempRange[0][0]
            if tempRange[0][1] < tempConfig['max_value']:
                config['variables'][0]["v1"]["ranges"][tempIdx]['x'+str(tempIdx+1)]['max_value'] = tempRange[0][1]

        if vehicle == "delivery":
            tempConfig = config['variables'][1]["v2"]["ranges"][tempIdx]['x'+str(tempIdx+1)]

            if tempRange[0][0] > tempConfig['min_value']:
                config['variables'][1]["v2"]["ranges"][tempIdx]['x'+str(tempIdx+1)]['min_value'] = tempRange[0][0]
            if tempRange[0][1] < tempConfig['max_value']:
                config['variables'][1]["v2"]["ranges"][tempIdx]['x'+str(tempIdx+1)]['max_value'] = tempRange[0][1]
        
    return config
       

# def updateOptions1(simulationResults, config):
#     for idx, item in enumerate(simulationResults):
#         if idx == 0:
#             lowest = sum(item[-5:])
#             lowest_idx = 0
#         else:
#             if sum(item[-5:]) < lowest:
#                 lowest = sum(item[-5:])
#                 lowest_idx = idx
    
#     for i in range(len(config['variables'])):
#         config['variables'][i]['x'+str(i+1)]['min_value'] = simulationResults[lowest_idx][i]
    
#     return config

def calculatePercentage(sims):
    sims_vio_t = 0
    sims_no_vio_accel = 0

    for item in sims:
        if item[-2] == 0 and item[-3] == 0 and item[-4] == 0:
            sims_no_vio_accel += 1

            if item[-1] >= 1:
                sims_vio_t += 1
    
    return sims_vio_t / sims_no_vio_accel

def useit(config, test, vehicle):
    if vehicle == "taxi":
        variable = config["variables"][0]["v1"]['ranges']
    if vehicle == "delivery":
        variable = config["variables"][1]['v2']['ranges']

    threshold = config["products"]
    repeat = config["control"][2]['c3']["value"]
    
    # generate n sims
    sims, _ = gen_sim(variable, repeat, test, vehicle)
    
    for item in sims:
        print(item)
    
    # generate violation
    if vehicle == "taxi":
        vehicle_type = 1
    if vehicle == "delivery":
        vehicle_type = 2
        
    sims_vio = violation(sims, threshold, vehicle_type)
    
    # generate violation learner table
    ##############################################################################
    ### choice = 1 : senario 1 - count number of violations in each goal       ###
    ### choice = 2 : senario 2 - if violation exists, then 1, o.w. 0           ###
    ### choice = 3 : senario 3 - only 1 goal, count all numbers of violations  ###
    ### choice = 4 : senario 4 - only 1 goal, if any violation, then 1, o.w. 0 ###
    ##############################################################################
    choice = 1 
    sims_final = goal_generate(sims_vio, choice)

    # test 6/9 uncomment this
    # percentage = calculatePercentage(sims_final)
    # print("Recommended percentage: ", percentage)

    return sims_final

def showResults(sims_final):
    # pretty print
    print("")
    [print(', '.join(x for x in header_row))]
    [print(', '.join([str(x) for x in lst])) for lst in sims_final]
    print("")

def main(option = None, test = None, vehicle = None):
    # define vehicle type (taxi, package, scout)
    print("Recommend: ", vehicle)
    
    # read configuration
    config0 = read_config(option)
    output_dict = {}
    for idx, run in enumerate(["optimize", "monitor", "safety"]):
        config = copy.deepcopy(config0)
        print("")
        print("Recommended for", run)
        config["hall"][1]["p2"]["value"] = idx+1
        result_dict = worker(config, test, vehicle)

        output_dict.update({run: result_dict})
    
    return output_dict
        


def cli():
    print("usage:")
    print("-c [config file name]: run simulations from specific configuration file")
    print("-t: run tests (option)")
    print("-v [taxi/delivery]: select vehicle (default taxi)")
    print("")

    # default sys argv
    option = "config.yaml"
    test = False
    vehicle = "taxi"

    # if len(sys.argv) == 4 and sys.argv[1] == "-c" and sys.argv[3] == "-t":
    #     option = sys.argv[2]
    #     test = True
    #     main(option, test, vehicle)
    # elif len(sys.argv) > 1 and sys.argv[1] == "-c":
    #     if len(sys.argv) == 2:
    #         print("")
    #         print("ERROR: please specify the configuration file!")
    #     else:
    #         option = sys.argv[2]
    #         main(option, test, vehicle)
    # elif len(sys.argv) > 1 and sys.argv[1] == "-t":
    #     test = True
    #     main(option, test, vehicle)
    # elif len(sys.argv) > 1 and (sys.argv[1] == "-v" or sys.argv[3] == "-v" or sys.argv[5] == "-v"):
    #     if sys.argv[1] == "-v":
    #         vehicle = sys.argv[2]
    #     elif sys.argv[3] == "-v":
    #         vehicle = sys.argv[4]
    #     elif sys.argv[5] == "-v":
    #         vehicle = sys.argv[6]

    #     main(option, test, vehicle)
    
    # updated sys.argv
    if len(sys.argv) > 1:
        if "-c" in sys.argv:
            option = sys.argv[sys.argv.index("-c")+1]
        if "-t" in sys.argv:
            test = True
        if "-v" in sys.argv:
            vehicle = sys.argv[sys.argv.index("-v")+1]

    output_dict = main(option, test, vehicle)

    with open("sample.json", "w") as outfile:
        json.dump(output_dict, outfile)

if __name__ == "__main__": cli()


