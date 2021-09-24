import {Component, ViewChild} from '@angular/core';
import {FormBuilder, FormGroup} from '@angular/forms';
import {HttpClient} from '@angular/common/http';
import {TEST} from '../test-input'
import {TEST_MONITOR} from '../test-monitor'
import {TEST_OPTIMIZE} from '../test-optimize'
import {TEST_SAFETY} from '../test-safety'
import {TEST_HEATMAP} from '../test-heatmap'
import {TEST_RANGE} from '../test-range'
import {TEST_GRAPH_DATA} from '../test-graph-data'
import {UIChart} from 'primeng/primeng';
import {ChartComponent} from 'ng-apexcharts';
import {__core_private_testing_placeholder__} from '@angular/core/testing';
import {Chart} from 'chart.js';
import * as ChartAnnotation from 'chartjs-plugin-annotation';
import axios from 'axios';

const DEFAULT_COLORS = ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099',
  '#3B3EAC', '#0099C6', '#DD4477', '#66AA00', '#B82E2E',
  '#316395', '#994499', '#22AA99', '#AAAA11', '#6633CC',
  '#E67300', '#8B0707', '#329262', '#5574A6', '#3B3EAC']

interface Type {
  name: string
  code: string
}

const STAR_HIGHLIGHT = "(*)"

@Component({
  selector: 'at-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})

export class DashboardComponent {
  names: Type[]
  graphOptions: Type[]
  selectedGraphOption: Type
  selectedName: Type
  selectedHeatmapX: string
  selectedHeatmapY: string

  sigAttributeHeaderModeText: string
  graphAscentAngleTitle: string
  graphDescentAngle1Title: string
  graphDescentAngle2Title: string
  graphCruiseSpeedTitle: string
  graphWindTitle: string
  graphTripDistanceTitle: string
  graphPayloadTitle: string
  graphCruiseAltitudeTitle: string
  graphWindDirectionTitle: string

  postId: any    // Stores Response
  DEFAULT: any
  boundaries: any
  rules: any
  heatmapData: any
  sigAttributeText: string
  dashboardForm: FormGroup

  @ViewChild('ascendAngleChart') ascendAngleChart: UIChart
  @ViewChild('descendAngle1Chart') descendAngle1Chart: UIChart
  @ViewChild('descendAngle2Chart') descendAngle2Chart: UIChart
  @ViewChild('cruiseSpeedChart') cruiseSpeedChart: UIChart
  @ViewChild('windChart') windChart: UIChart
  @ViewChild('tripDistanceChart') tripDistanceChart: UIChart
  @ViewChild('payloadChart') payloadChart: UIChart
  @ViewChild('cruiseAltitudeChart') cruiseAltitudeChart: UIChart
  @ViewChild('windDirectionChart') windDirectionChart: UIChart

  attributes = [
    {label: "Ascent Angle", origLabel: "Ascent Angle", value: "ascend_angle"},
    {label: "Descent Angle Rapid", origLabel: "Descent Angle Rapid", value: "descend_angle_1"},
    {label: "Descent Angle Slow", origLabel: "Descent Angle Slow", value: "descend_angle_2"},
    {label: "Cruise Speed", origLabel: "Cruise Speed", value: "cruise_speed"},
    {label: "Wind", origLabel: "Wind", value: "wind"},
    {label: "Trip Distance", origLabel: "Trip Distance", value: "trip_distance"},
    {label: "Payload", origLabel: "Payload", value: "payload"},
    {label: "Cruise Altitude", origLabel: "Cruise Altitude", value: "cruise_altitude"},
    {label: "Wind Direction", origLabel: "Wind Direction", value: "direction"}
  ]

  // Default constructor
  constructor(private fb: FormBuilder, private http: HttpClient) {
  }

  // ApexCharts HeatMap
  @ViewChild('heatmap') heatmap: ChartComponent;
  heatmapOptions = {
    id: 'heatmap',
    series: [],
    chart: {
      height: 350,
      type: 'heatmap',
      animations: {enabled: false}
    },
    dataLabels: {
      enabled: false
    },
    colors: ['#E91E63'],
    title: {
      text: ''
    },
    xaxis: {
      title: {
        text: ''
      }
    },
    yaxis: {
      title: {
        text: ''
      }
    },
    plotOptions: {
      heatmap: {
        enableShades: false,
        colorScale: {
          ranges: []
        }
      }
    }
  };

  public generateData(count, yrange) {
    var i = 0;
    var series = [];
    while (i < count) {
      var x = 'w' + (i + 1).toString();
      var y =
        Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

      series.push({
        x: x,
        y: y
      });
      i++;
    }
    return series;
  }

  // Set graph attributes for all graphs
  graphDisplayOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 5,
        xMax: 25,
        backgroundColor: ''
      }]
    }
  }

  // Scatter plot data & options
  ascendAngleData = {
    datasets: [
      {
        label: 'Ascend Angle',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true,
      },
    ],
  }
  ascendAngleOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  descendAngle1Data = {
    datasets: [
      {
        label: 'Descent Angle',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  descendAngle1Options = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  descendAngle2Data = {
    datasets: [
      {
        label: 'Descent Angle',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  descendAngle2Options = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  cruiseSpeedData = {
    datasets: [
      {
        label: 'Cruise Speed (m/s)',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  cruiseSpeedOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  windData = {
    datasets: [
      {
        label: 'Wind (m/s)',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  windOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  tripDistanceData = {
    datasets: [
      {
        label: 'Trip Distance (m)',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  tripDistanceOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  payloadData = {
    datasets: [
      {
        label: 'Playload (lb)',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  payloadOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  cruiseAltitudeData = {
    datasets: [
      {
        label: 'Cruise Altitude (m)',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  cruiseAltitudeOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  windDirectionData = {
    datasets: [
      {
        label: 'Wind Direction',
        backgroundColor: DEFAULT_COLORS[0],
        data: [],
        fill: false,
        showLine: true
      },
    ]
  }
  windDirectionOptions = {
    animation: {
      duration: 0
    },
    legend: {
      display: false,
      position: 'bottom'
    },
    scales: {
      xAxes: [{
        display: true,
        id: 'x-axis-0',
      }],
      yAxes: [{
        scaleLabel: {
          display: true,
          labelString: 'P (non-violations)'
        }
      }]
    },
    annotation: {
      annotations: [{
        type: 'box',
        xScaleID: 'x-axis-0',
        xMin: 0,
        xMax: 0,
        backgroundColor: ''
      }]
    }
  }

  // Import file (Not currently used)
  async fileChangeListener($event: any): Promise<void> {
    // Import file here
    const files = $event.srcElement.files;
    fetch(files[0]).then(response => console.log(response))
    let fileText = await files[0].text()
  }

  // Runs when you hit the submit button
  onRun(){
    const parameters = this.setParameters(TEST, this.dashboardForm.value)
    alert('Sending parameters')
    console.log('API call query',)

    axios.post(this.dashboardForm.value.backendUrl, parameters)
      .then((response) => {
        // Set Attributes
        this.setGraphsData(response.data['attribute_percentage'])
        this.boundaries = response.data['outputs']
        this.rules = response.data['all_rules']

        // Heatmap data
        this.heatmapData = response.data['joint_attribute_percentage']
        this.setHeatmapData(this.heatmapData)

        // Refresh
        alert('Graph data received')
        console.log("Graph data received")
        this.onGraphModeChange()
      }, (error) => {
        console.log(error);
      });
  }

  // Copy the form fields to a submittable format
  setParameters(parameters: any, form: any) {
    parameters.options.variables[0].v1.ranges[0].x1.max_value = Number(form.ascentAngleMax)
    parameters.options.variables[0].v1.ranges[0].x1.min_value = Number(form.ascentAngleMin)
    parameters.options.variables[0].v1.ranges[1].x2.max_value = Number(form.descendAngle1Max)
    parameters.options.variables[0].v1.ranges[1].x2.min_value = Number(form.descendAngle1Min)
    parameters.options.variables[0].v1.ranges[2].x3.max_value = Number(form.descendAngle2Max)
    parameters.options.variables[0].v1.ranges[2].x3.min_value = Number(form.descendAngle2Min)
    parameters.options.variables[0].v1.ranges[3].x4.max_value = Number(form.cruiseSpeedMax)
    parameters.options.variables[0].v1.ranges[3].x4.min_value = Number(form.cruiseSpeedMin)
    parameters.options.variables[0].v1.ranges[4].x5.max_value = Number(form.tripDistanceMax)
    parameters.options.variables[0].v1.ranges[4].x5.min_value = Number(form.tripDistanceMin)
    parameters.options.variables[0].v1.ranges[5].x6.max_value = Number(form.cruiseAltitudeMax)
    parameters.options.variables[0].v1.ranges[5].x6.min_value = Number(form.cruiseAltitudeMin)
    parameters.options.variables[0].v1.ranges[6].x7.max_value = Number(form.payloadMax)
    parameters.options.variables[0].v1.ranges[6].x7.min_value = Number(form.payloadMin)
    parameters.options.variables[0].v1.ranges[7].x8.max_value = Number(form.windMax)
    parameters.options.variables[0].v1.ranges[7].x8.min_value = Number(form.windMin)
    parameters.options.variables[0].v1.ranges[8].x9.max_value = Number(form.directionMax)
    parameters.options.variables[0].v1.ranges[8].x9.min_value = Number(form.directionMin)

    parameters.options.products[0].y1.rules[1].r2.value = Number(form.longitudnalAcceleration)
    parameters.options.products[0].y1.rules[2].r3.value = Number(form.lateralAcceleration)
    parameters.options.products[0].y1.rules[3].r4.value = Number(form.jerk)
    parameters.options.products[0].y1.rules[4].r5.value = Number(form.charging)

    return parameters
  }

  // Refresh Scatterplots / Heatmaps / Significant Attributes
  onGraphModeChange() {
    let boundaryData = null
    let boundaryColor = null
    switch(this.dashboardForm.value.graphMode){
      case "M":
        boundaryColor = 'rgba(248, 105, 107, 0.25)'    
        boundaryData = this.boundaries.monitor.r_extra
        break
      case 'O':
        boundaryColor = 'rgba(181, 214, 128, 0.25)'
        boundaryData = this.boundaries.optimize.r_extra
        if(this.rules) this.setSignificantAttributes(this.rules, "optimize")
        if(this.heatmapData) this.setHeatmapData(this.heatmapData)
        this.sigAttributeHeaderModeText = "Optimize"
        break
      case 'S':
        boundaryColor = 'rgba(247, 233, 132, 0.25)'
        boundaryData = this.boundaries.safety.r_extra
        if(this.rules) this.setSignificantAttributes(this.rules, "monitor")
        if(this.heatmapData) this.setHeatmapData(this.heatmapData)
        this.sigAttributeHeaderModeText = "Suggestion"
        break
    }
    this.setBoundaries(boundaryData, boundaryColor)
    this.refreshScatterPlotsAll()
  }

  // Refresh Heatmap
  onHeatmapChange(){
    this.setHeatmapData(this.heatmapData)
  }

  // Helper function to convert JSON listing to Heatmap Data
  setHeatmapData(dataset: any) { 
    const heatmapX = this.dashboardForm.value.heatmapX
    const heatmapY = this.dashboardForm.value.heatmapY
    let index = 0
    for (var i = 0; i < dataset[heatmapX].length; i++) {
      if (heatmapY == Object.keys(dataset[heatmapX][i])[0]) {
        index = i
        break
      }
    }

    // Re-wire data to the heatmap
    const data = dataset[heatmapX][index][heatmapY]
    let rowCountMax = Object.keys(dataset[heatmapX][index][heatmapY]).length
    let rowCount = 0
    let objList = [] as any
    for (const row in data) {
      // Only label every few rows
      const rowLabel = (
        rowCount == 0
        || rowCount == rowCountMax - 1
        || rowCount % 4 == 0
      ) ? row : ''
      rowCount++
      const rowObj = {name: rowLabel, data: data[row]}
      objList.push(rowObj)
    }

    // Set color scheme
    // Must get max & min
    let yMin = 1
    let yMax = 0
    for (const row in objList) {
      objList[row].data.forEach(e => {
        if (e.y > yMax) {
          yMax = e.y
        }
        if (e.y < yMin) {
          yMin = e.y
        }
      })
    }

    // Now make color ranges
    const range = yMax - yMin
    const step = range / 5
    const colorRanges = []
    colorRanges.push({from: 0, to: step, color: '#f8696b', name: 'low'})
    colorRanges.push({from: step, to: 2*step, color: '#fa9b74', name: 'mid-low'})
    colorRanges.push({from: 2*step, to: 3*step, color: '#f7e984', name: 'mid'})
    colorRanges.push({from: 3*step, to: 4*step, color: '#cbdc81', name: 'mid-high'})
    colorRanges.push({from: 4*step, to: yMax, color: '#63be7b', name: 'high'})

    // Set Labels
    let xAxisLabel = this.attributes.filter(e => {return e.value === heatmapX})[0].label
    let yAxisLabel = this.attributes.filter(e => {return e.value === heatmapY})[0].label

    // Refresh heatmap (Updates automatically)
    this.heatmapOptions = {
      ...this.heatmapOptions,
      series: objList,
      title: {text: `X: ${xAxisLabel} & Y: ${yAxisLabel}`},
      xaxis: {title: {text: xAxisLabel}},
      yaxis: {title: {text: yAxisLabel}},
      plotOptions: {heatmap: {enableShades: false, colorScale: {ranges: colorRanges}}}
    }
  }

  // Helper function to convert JSON listing to chart coordinates
  jsonToCoords(obj: any) {
    return Object.keys(obj)
      .map(key =>
        ({
          x: Number(key),
          y: obj[key]
        }))
  }

  // Helper function to change boundary ranges and color
  setBoundaries(data: any, color: string) {
    // Change boundaries
    this.ascendAngleOptions.annotation.annotations[0].xMin = data.ascend_angle[0]
    this.ascendAngleOptions.annotation.annotations[0].xMax = data.ascend_angle[1]
    this.descendAngle1Options.annotation.annotations[0].xMin = data.descend_angle_1[0]
    this.descendAngle1Options.annotation.annotations[0].xMax = data.descend_angle_1[1]
    this.descendAngle2Options.annotation.annotations[0].xMin = data.descend_angle_2[0]
    this.descendAngle2Options.annotation.annotations[0].xMax = data.descend_angle_2[1]

    this.cruiseSpeedOptions.annotation.annotations[0].xMin = data.cruise_speed[0]
    this.cruiseSpeedOptions.annotation.annotations[0].xMax = data.cruise_speed[1]
    this.windOptions.annotation.annotations[0].xMin = data.wind[0]
    this.windOptions.annotation.annotations[0].xMax = data.wind[1]
    this.tripDistanceOptions.annotation.annotations[0].xMin = data.trip_distance[0]
    this.tripDistanceOptions.annotation.annotations[0].xMax = data.trip_distance[1]

    this.payloadOptions.annotation.annotations[0].xMin = data.payload[0]
    this.payloadOptions.annotation.annotations[0].xMax = data.payload[1]
    this.cruiseAltitudeOptions.annotation.annotations[0].xMin = data.cruise_altitude[0]
    this.cruiseAltitudeOptions.annotation.annotations[0].xMax = data.cruise_altitude[1]
    this.windDirectionOptions.annotation.annotations[0].xMin = data.direction[0]
    this.windDirectionOptions.annotation.annotations[0].xMax = data.direction[1]

    // Change the colors
    this.ascendAngleOptions.annotation.annotations[0].backgroundColor = color
    this.descendAngle1Options.annotation.annotations[0].backgroundColor = color
    this.descendAngle2Options.annotation.annotations[0].backgroundColor = color
    this.cruiseSpeedOptions.annotation.annotations[0].backgroundColor = color
    this.windOptions.annotation.annotations[0].backgroundColor = color
    this.tripDistanceOptions.annotation.annotations[0].backgroundColor = color
    this.payloadOptions.annotation.annotations[0].backgroundColor = color
    this.cruiseAltitudeOptions.annotation.annotations[0].backgroundColor = color
    this.windDirectionOptions.annotation.annotations[0].backgroundColor = color
  }

  // Highlights the most noteworthy attributes with a (*) star
  highlightAttributeMenu(sigAttributeList: any){
    this.attributes.map(e => e.label = e.origLabel)
    sigAttributeList.map(
      (sigAttribute: string[]) =>{
        const oldLabel = this.attributes.filter(e => {return e.value === sigAttribute[1][0].toLowerCase()})[0].label
        this.attributes.filter(e => {
          return e.value === sigAttribute[1][0].toLowerCase()
        })[0].label = oldLabel.includes("(*)") ? oldLabel : oldLabel + " (*)"        
      }
    )
  }

  // Helper function to change the featured regions in the graphs
  setGraphsData(data: any) {
    this.ascendAngleData.datasets[0].data = this.jsonToCoords(data.ascend_angle)
    this.descendAngle1Data.datasets[0].data = this.jsonToCoords(data.descend_angle_1)
    this.descendAngle2Data.datasets[0].data = this.jsonToCoords(data.descend_angle_2)
    this.cruiseSpeedData.datasets[0].data = this.jsonToCoords(data.cruise_speed)
    this.windData.datasets[0].data = this.jsonToCoords(data.wind)
    this.tripDistanceData.datasets[0].data = this.jsonToCoords(data.trip_distance)
    this.payloadData.datasets[0].data = this.jsonToCoords(data.payload)
    this.cruiseAltitudeData.datasets[0].data = this.jsonToCoords(data.cruise_altitude)
    this.windDirectionData.datasets[0].data = this.jsonToCoords(data.direction)
  }

  // Helper function to refresh scatter plots
  refreshScatterPlotsAll() {
    this.ascendAngleChart.reinit()
    this.descendAngle1Chart.reinit()
    this.descendAngle2Chart.reinit()
    this.cruiseSpeedChart.reinit()
    this.windChart.reinit()
    this.tripDistanceChart.reinit()
    this.payloadChart.reinit()
    this.cruiseAltitudeChart.reinit()
    this.windDirectionChart.reinit()
  }

  // Helper function to populate heatmaps and significant attributes
  setSignificantAttributes(rules: any, mode: string) {
    const sigAttributeList = this.rules[mode].r1

    // Set heatmap X-axis
    const numSigAttributes = sigAttributeList.length
    const sigAttributeX = sigAttributeList[0][1][0].toLowerCase()
    this.dashboardForm.value.heatmapX = sigAttributeX

    // Set heatmap Y-axis if there are 2+ attributes
    if(numSigAttributes >= 2){
      const sigAttributeY = sigAttributeList[1][1][0].toLowerCase()
      this.dashboardForm.value.heatmapY = sigAttributeY
    }    
    
    this.graphAscentAngleTitle = ""
    this.graphDescentAngle1Title = ""
    this.graphDescentAngle2Title = ""
    this.graphCruiseSpeedTitle = ""
    this.graphWindTitle = ""
    this.graphTripDistanceTitle = ""
    this.graphPayloadTitle = ""
    this.graphCruiseAltitudeTitle = ""
    this.graphWindDirectionTitle = ""
    
    sigAttributeList.map(attribute =>
      {
        switch(attribute[1][0]){
          case "Ascend_angle":
            this.graphAscentAngleTitle = STAR_HIGHLIGHT
            break
          case "Descend_angle_1":
            this.graphDescentAngle1Title = STAR_HIGHLIGHT
            break
          case "Descend_angle_2":
            this.graphDescentAngle2Title = STAR_HIGHLIGHT
            break
          case "Cruise_speed":
            this.graphCruiseSpeedTitle = STAR_HIGHLIGHT
            break
          case "Wind":
            this.graphWindTitle= STAR_HIGHLIGHT
            break
          case "Trip_distance":
            this.graphTripDistanceTitle = STAR_HIGHLIGHT
            break
          case "Payload":
            this.graphPayloadTitle = STAR_HIGHLIGHT
            break
          case "Cruise_altitude":
            this.graphCruiseAltitudeTitle = STAR_HIGHLIGHT
            break
          case "Direction":
            this.graphWindDirectionTitle = STAR_HIGHLIGHT
            break
          default:
            console.log("Attribute not found!")
            break
        }
      })


    // Modify modules based on significant attributes
    let significantFormatText = ""
    sigAttributeList.map(rule => 
      { 
        significantFormatText += (rule[0] + "  -  " + rule[1][0] + ":    " + rule[1][1][0] + " to " + rule[1][1][1] + "\n")
      })
    this.sigAttributeText = significantFormatText
    this.highlightAttributeMenu(sigAttributeList)
  }


  // Debug button (when used)
  onDebug() {
    alert('Input object shown to Console.log()')
  }

  // Initialization on site load
  ngOnInit(){
    // Set up Chart.js annotations
    let namedChartAnnotation = ChartAnnotation
    namedChartAnnotation['id'] = 'annotation'
    Chart.pluginService.register(namedChartAnnotation)

    // Setup fields for other modules
    this.dashboardForm = this.fb.group({
      name: 'taxi',
      ascentAngleMax: [TEST.options.variables[0].v1.ranges[0].x1.max_value],
      ascentAngleMin: [TEST.options.variables[0].v1.ranges[0].x1.min_value],
      descendAngle1Max: [TEST.options.variables[0].v1.ranges[1].x2.max_value],
      descendAngle1Min: [TEST.options.variables[0].v1.ranges[1].x2.min_value],
      descendAngle2Max: [TEST.options.variables[0].v1.ranges[2].x3.max_value],
      descendAngle2Min: [TEST.options.variables[0].v1.ranges[2].x3.min_value],
      cruiseSpeedMax: [TEST.options.variables[0].v1.ranges[3].x4.max_value],
      cruiseSpeedMin: [TEST.options.variables[0].v1.ranges[3].x4.min_value],
      tripDistanceMax: [TEST.options.variables[0].v1.ranges[4].x5.max_value],
      tripDistanceMin: [TEST.options.variables[0].v1.ranges[4].x5.min_value],
      cruiseAltitudeMax: [TEST.options.variables[0].v1.ranges[5].x6.max_value],
      cruiseAltitudeMin: [TEST.options.variables[0].v1.ranges[5].x6.min_value],
      payloadMax: [TEST.options.variables[0].v1.ranges[6].x7.max_value],
      payloadMin: [TEST.options.variables[0].v1.ranges[6].x7.min_value],
      windMax: [TEST.options.variables[0].v1.ranges[7].x8.max_value],
      windMin: [TEST.options.variables[0].v1.ranges[7].x8.min_value],
      directionMax: [TEST.options.variables[0].v1.ranges[8].x9.max_value],
      directionMin: [TEST.options.variables[0].v1.ranges[8].x9.min_value],
      longitudnalAcceleration: [TEST.options.products[0].y1.rules[1].r2.value],
      lateralAcceleration: [TEST.options.products[0].y1.rules[2].r3.value],
      jerk: [TEST.options.products[0].y1.rules[3].r4.value],
      charging: [TEST.options.products[0].y1.rules[4].r5.value],
      graphMode: ['O'],
      heatmapX: ['cruise_speed'],
      heatmapY: ['ascend_angle'],
      backendUrl: "http://127.0.0.1:5000/v3/bestRules-sample"
      // backendUrl: "http://127.0.0.1:5000/v2/bestRules"
    })
    this.names = [
      {name: 'Taxi', code: 'tx'},
      {name: 'Drone Delivery', code: 'dd'}
    ]
    this.graphOptions = [
      {name: 'Monitor', code: 'm'},
      {name: 'Optimize', code: 'o'},
      {name: 'Safety', code: 's'}
    ]
    this.sigAttributeText = "(Click Run)"

    // Set Label titles
    this.sigAttributeHeaderModeText = "Optimize"
    this.graphAscentAngleTitle = ""
    this.graphDescentAngle1Title = ""
    this.graphDescentAngle2Title = ""
    this.graphCruiseSpeedTitle = ""
    this.graphWindTitle = ""
    this.graphTripDistanceTitle = ""
    this.graphPayloadTitle = ""
    this.graphCruiseAltitudeTitle = ""
    this.graphWindDirectionTitle = ""

    // Obtain initial graph data (from MONITOR)
    this.DEFAULT = TEST
    this.boundaries = TEST_RANGE
    this.setHeatmapData(TEST_HEATMAP)
    this.setGraphsData(TEST_GRAPH_DATA)
    this.onGraphModeChange()
  }
}


