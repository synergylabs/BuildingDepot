'use strict';
let autocannon = require('autocannon'),
    fileSystemHandler = require("./fileSystemHandler");
var sensors = [];
sensors = [];


/**
 * Save the sensor list.
 */
let saveSensors = async function (sensors) {
    let filename = 'sensors.json';
    await fs.writeFile(filename, JSON.stringify(sensors));
};

let runTest = async function (options) {
    return new Promise(resolve => {
        let finishedBench = async function (err, res) {
            if (res) {
                await fileSystemHandler.writeDataToFile('./', 'sensors.json', JSON.stringify(sensors));
                console.log(sensors.length + ' new sensor(s) created.');
                resolve(true)
            }
        };
        let instance = autocannon(options, finishedBench);
        autocannon.track(instance);
        // Fuction that handles the responses
        instance.on('response', handleResponse);

        // Handle individual response
        function handleResponse(client, statusCode, resBytes, responseTime) {
            let response = client.parser.chunk.toString();
            let apiResponseString = response.substring(response.indexOf('{'));
            if (apiResponseString[0] === '{') {
                let apiResponse = JSON.parse(apiResponseString);
                if (apiResponse.success === 'True') {
                    sensors.push(apiResponse.uuid);
                }
            }
        }
    })
};

module.exports = {
    runTest: runTest
};