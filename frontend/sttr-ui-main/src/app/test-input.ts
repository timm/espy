export const TEST = {
    "output": "taxi",
    "options": {
      "variables": [
        {
          "v1": {
            "name": "taxi",
            "ranges": [
              {
                "x1": {
                  "name": "Ascend_angle",
                  "min_value": 3,
                  "max_value": 30,
                  "units": "radians",
                  "handle": "alpha",
                  "goal": "None",
                  "definition": "Angle between the oncoming air or relative wind and a reference line on the airplane or wing",
                  "input": "None",
                  "Output": "x/y/z position",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x2": {
                  "name": "Descend_angle_1",
                  "min_value": 6,
                  "max_value": 30,
                  "units": "radians",
                  "handle": "alpha_d1",
                  "goal": "None",
                  "definition": "Angle between the oncoming air or relative wind and a reference line on the airplane or wing",
                  "input": "None",
                  "Output": "x/y/z position",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x3": {
                  "name": "Descend_angle_2",
                  "min_value": 3,
                  "max_value": 27,
                  "units": "radians",
                  "handle": "alpha_d1",
                  "goal": "None",
                  "definition": "Angle between the oncoming air or relative wind and a reference line on the airplane or wing",
                  "input": "None",
                  "Output": "x/y/z position",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x4": {
                  "name": "Cruise_speed",
                  "min_value": 50,
                  "max_value": 300,
                  "units": "m/s",
                  "handle": "v_c",
                  "goal": "max",
                  "definition": "The specific airspeed that an aircraft flies at when enroute",
                  "input": "None",
                  "Output": "x/y/z velocity",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x5": {
                  "name": "Trip_distance",
                  "min_value": 5000,
                  "max_value": 30000,
                  "units": "m",
                  "handle": "d",
                  "goal": "None",
                  "definition": "A ground-based measurement from the aircraft's starting to location (before takeoff) to the point where the aircraft lands",
                  "input": "None",
                  "Output": "x/y position",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x6": {
                  "name": "Cruise_altitude",
                  "min_value": 100,
                  "max_value": 1000,
                  "units": "m",
                  "handle": "h",
                  "goal": "None",
                  "definition": "The height measured from sea level to the point in the atmosphere where the aircraft initially reaches its cruising speed",
                  "input": "None",
                  "Output": "z position",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x7": {
                  "name": "Payload",
                  "min_value": 0,
                  "max_value": 2000,
                  "units": "kg",
                  "handle": "wp",
                  "goal": "None",
                  "definition": "The wright of any materials that does not include the aircraft. This could include cargo, passengers, fight crew, instruments, and more",
                  "input": "None",
                  "Output": "energy requirement",
                  "Notes": "None",
                  "Usage": "Controllable"
                }
              },
              {
                "x8": {
                  "name": "Wind",
                  "min_value": 0,
                  "max_value": 30,
                  "units": "m/s",
                  "handle": "v_infinite",
                  "goal": "None",
                  "definition": "The rate at which air is travelling",
                  "input": "None",
                  "Output": "x/y velocity",
                  "Notes": "None",
                  "Usage": "Observable"
                }
              },
              {
                "x9": {
                  "name": "Direction",
                  "min_value": 0,
                  "max_value": 180,
                  "units": "None",
                  "handle": "None",
                  "goal": "None",
                  "definition": "None",
                  "input": "None",
                  "Output": "None",
                  "Notes": "None",
                  "Usage": "None"
                }
              }
            ]
          }
        },
      ],
      "products": [
        {
          "y1": {
            "name": "taxi",
            "rules": [
              {
                "r1": {
                  "name": "t",
                  "min_value": 0,
                  "max_value": 0,
                  "value": 0
                }
              },
              {
                "r2": {
                  "name": "long_accel",
                  "min_value": 1,
                  "max_value": 1.5,
                  "value": 1
                }
              },
              {
                "r3": {
                  "name": "lat_accel",
                  "min_value": 1,
                  "max_value": 1.5,
                  "value": 1
                }
              },
              {
                "r4": {
                  "name": "jerk",
                  "min_value": 0.3,
                  "max_value": 0.6,
                  "value": 0.3
                }
              },
              {
                "r5": {
                  "name": "charging",
                  "min_value": 0.2,
                  "max_value": 0.25,
                  "value": 0.2
                }
              }
            ]
          }
        },
        {
          "y2": {
            "name": "organ delivery",
            "rules": [
              {
                "r1": {
                  "name": "t",
                  "min_value": 0,
                  "max_value": 0,
                  "value": 0
                }
              },
              {
                "r2": {
                  "name": "long_accel",
                  "min_value": 1,
                  "max_value": 1.5,
                  "value": 1
                }
              },
              {
                "r3": {
                  "name": "lat_accel",
                  "min_value": 1,
                  "max_value": 1.5,
                  "value": 1
                }
              },
              {
                "r4": {
                  "name": "jerk",
                  "min_value": 0.3,
                  "max_value": 0.6,
                  "value": 0.3
                }
              },
              {
                "r5": {
                  "name": "charging",
                  "min_value": 0.2,
                  "max_value": 0.25,
                  "value": 0.2
                }
              }
            ]
          }
        }
      ],
      "control": [
        {
          "c1": {
            "name": "vehicle_type",
            "value_1": "taxi",
            "value_2": "package",
            "value": "taxi"
          }
        },
        {
          "c2": {
            "name": "generations",
            "min_value": 1,
            "max_value": 10,
            "value": 10
          }
        },
        {
          "c3": {
            "name": "samples",
            "min_value": 1000,
            "max_value": 100000,
            "value": 5000
          }
        },
        {
          "c4": {
            "name": "seed",
            "min_value": 1,
            "max_value": 100013,
            "value": 1
          }
        }
      ],
      "hall": [
        {
          "p1": {
            "name": "elite",
            "min_value": 2,
            "max_value": 7,
            "value": 2
          }
        },
        {
          "p2": {
            "name": "act",
            "min_value": 1,
            "max_value": 3,
            "value": 1
          }
        },
        {
          "p3": {
            "name": "yround",
            "min_value": 1,
            "max_value": 3,
            "value": 2
          }
        },
        {
          "p4": {
            "name": "cohen",
            "min_value": 0,
            "max_value": 1,
            "value": 0.3
          }
        },
        {
          "p5": {
            "name": "size",
            "min_value": 0,
            "max_value": 1,
            "value": 0.5
          }
        },
        {
          "p6": {
            "name": "k",
            "min_value": 1,
            "max_value": 5,
            "value": 1
          }
        },
        {
          "p7": {
            "name": "m",
            "min_value": 1,
            "max_value": 5,
            "value": 2
          }
        },
        {
          "p8": {
            "name": "top",
            "min_value": 1,
            "max_value": 20,
            "value": 10
          }
        },
        {
          "p9": {
            "name": "show",
            "min_value": 1,
            "max_value": 20,
            "value": 10
          }
        },
        {
          "p10": {
            "name": "minSupport",
            "min_value": 0,
            "max_value": 1,
            "value": 0.4
          }
        }
      ]
    }
}