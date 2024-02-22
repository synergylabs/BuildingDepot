/**
 * Created by sud335 on 4/12/16.
 */

function generateChartData(data) {
    var chartData = [];
    for (var i = 0; i < data.length; i++) {
        var a = data[i][2];
        var b = data[i][2];
        if (typeof a === 'number' || a instanceof Number) {
            var newDate = data[i][0];
            chartData.push({
                date: newDate,
                value: a,
                volume: b
            });
        } else {
            var newDate = data[i][0];
            chartData.push({
                date: newDate,
                value: 1,
                volume: 1
            });
        }
    }
    return chartData;
}


function generateTextualData(data) {
    var textualData = [];
    for (var i = 0; i < data.length; i++) {
        var a = data[i][2];
        if (typeof a === 'string' || a instanceof String) {
            var newDate = data[i][0];
            textualData.push({
                date: new Date(newDate),
                type: "flag",
                backgroundColor: "#33ccff",
                backgroundAlpha: 0.5,
                graph: "g1",
                text: a,
                description: a
            });
        }
    }
    return textualData;
}

function makechart(data) {

    var chartData = generateChartData(data);
    var textualData = generateTextualData(data);
    var config = {
        "type": "stock",
        "theme": "light",

        "categoryAxesSettings": {
            "minPeriod": "fff"
        },
        "dataSets": [{
            "color": "#33ccff",
            "fieldMappings": [{
                "fromField": "value",
                "toField": "value"
            }, {
                "fromField": "volume",
                "toField": "volume"
            }],
            "dataProvider": chartData,
            "categoryField": "date",
            // EVENTS
            "stockEvents": textualData
        }],


        "panels": [{
            "showCategoryAxis": false,
            "title": "Data points",
            "percentHeight": 70,

            "stockGraphs": [{
                "id": "g1",
                "valueField": "value"
            }],


            "stockLegend": {
                "valueTextRegular": " ",
                "markerType": "none"
            }
        }, {
            "title": "Value",
            "percentHeight": 30,
            "stockGraphs": [{
                "valueField": "volume",
                "type": "column",
                "cornerRadiusTop": 2,
                "fillAlphas": 1
            }],

            "stockLegend": {
                "valueTextRegular": " ",
                "markerType": "none"
            }
        }],

        "chartScrollbarSettings": {
            "graph": "g1",
            "usePeriod": "10mm",
            "position": "top"
        },

        "chartCursorSettings": {
            "valueBalloonsEnabled": true,
        },

        "periodSelector": {
            "position": "top",
            "dateFormat": "YYYY-MM-DD JJ:NN",
            "inputFieldWidth": 150,
            "periods": [{
                "period": "mm",
                "count": 30,
                "label": "30 mins",
                "selected": true
            }, {
                "period": "hh",
                "count": 1,
                "label": "1 hour",
                "selected": true
            }, {
                "period": "hh",
                "count": 3,
                "label": "3 hour",
                "selected": true
            }, {
                "period": "hh",
                "count": 6,
                "label": "6 hour",
                "selected": true
            }, {
                "period": "hh",
                "count": 12,
                "label": "12 hours"
            }, {
                "period": "DD",
                "count": 1,
                "label": "1 day"
            }, {
                "period": "MM",
                "count": 1,
                "label": "1 month"
            }, {
                "period": "MM",
                "count": 6,
                "label": "6 months"
            }, {
                "period": "YYYY",
                "count": 1,
                "label": "1 year"
            }, {
                "period": "YYYY",
                "count": 3,
                "label": "3 years"
            }, {
                "selected": true,
                "period": "MAX",
                "label": "All"
            }]
        },

        "panelsSettings": {
            "usePrefixes": false
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    };
    var chart = AmCharts.makeChart("chartdiv", config);


}
