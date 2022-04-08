/**
 Copyright 2021. Corning Incorporated. All rights reserved.

 This software may only be used in accordance with the identified license(s).

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
 ==========================================================================
**/

module.exports = {
    runList: [
        {
            "Campus": "SP",
            "EntranceScreening": "false",
            "FacilityOccupancy": "0.12",
            "MaxRoomOccupancy": "1",
            "NumberOfEmployees": "0",
            "NumberOfEntrances": "1",
            "NumberOfExits": "1",
            "NumberOfFloors": "1",
            "NumberOfOneWayAisles": "0",
            "NumberOfShifts": "1",
            "SimulationName": "SP_32400_100",
            "TimestepInSec": "1",
            "sim_id": "SP_32400_100"
        },
        {
            "Campus": "SP_TD",
            "EntranceScreening": "false",
            "FacilityOccupancy": "0.12",
            "MaxRoomOccupancy": "1",
            "NumberOfEmployees": "0",
            "NumberOfEntrances": "1",
            "NumberOfExits": "1",
            "NumberOfFloors": "1",
            "NumberOfOneWayAisles": "0",
            "NumberOfShifts": "1",
            "SimulationName": "SP-FE-TD_7200_100",
            "TimestepInSec": "1",
            "sim_id": "SP-FE-TD_7200_100"
        }
    ],
    attList: ["TimestepInSec", "NumberOfFloors", "NumberOfOneWayAisles", "NumberOfEmployees", "SimulationName", "Campus",
        "FacilityOccupancy", "MaxRoomOccupancy", "NumberOfShifts", "NumberOfEntrances", "NumberOfExits",
        "EntranceScreening", "sim_id"],
    currSimId: "SP_32400_100",
    totalContactsPerAgentHistogram: [26, 7, 29, 33, 72, 49, 63, 11, 10, 24, 7, 19, 13, 40, 14, 23, 45, 19],
    totalContactsHistogramOption: {chartTitle: "Total Contact per Agent", chartCol: "#5290f1"},
    avgContactDurationPerAgentHistogram: ["0.88", "1.1", "0.72", "1.4", "0.81", "1.1", "0.87", "1.0", "1.4", "0.38", "0.86", "0.68", "0.46", "0.97", "0.86", "0.91", "0.89", "0.79"],
    avgContactDurationHistogramOption: {chartTitle: "Average Contact Duration minutes", chartCol: "#5fd0c7"},
    chartData: [
        {
            "a": "7",
            "x": 26,
            "y": "0.88"
        },
        {
            "a": "12",
            "x": 7,
            "y": "1.1"
        },
        {
            "a": "8",
            "x": 29,
            "y": "0.72"
        },
        {
            "a": "3",
            "x": 33,
            "y": "1.4"
        },
        {
            "a": "1",
            "x": 72,
            "y": "0.81"
        },
        {
            "a": "6",
            "x": 49,
            "y": "1.1"
        },
        {
            "a": "9",
            "x": 63,
            "y": "0.87"
        },
        {
            "a": "5",
            "x": 11,
            "y": "1.0"
        },
        {
            "a": "13",
            "x": 10,
            "y": "1.4"
        },
        {
            "a": "15",
            "x": 24,
            "y": "0.38"
        },
        {
            "a": "2",
            "x": 7,
            "y": "0.86"
        },
        {
            "a": "10",
            "x": 19,
            "y": "0.68"
        },
        {
            "a": "0",
            "x": 13,
            "y": "0.46"
        },
        {
            "a": "14",
            "x": 40,
            "y": "0.97"
        },
        {
            "a": "17",
            "x": 14,
            "y": "0.86"
        },
        {
            "a": "18",
            "x": 23,
            "y": "0.91"
        },
        {
            "a": "19",
            "x": 45,
            "y": "0.89"
        },
        {
            "a": "16",
            "x": 19,
            "y": "0.79"
        }
    ]

}
