let sensors = require('../sensors.json'),
    fileSystemHandler = require('./fileSystemHandler');

/**
 * Creates data for POST time-series API.
 * @return {string} JSON string for posting data to time-series API
 */
let formData = async function (saveFile = 'log.json', totalSensors = 300, totalSamples = 2, totalValues = 1, dynamic = false) {
    if (totalSensors > sensors.length) {
        console.log("Not enough sensor UUIDs to generate data. Use \"create sensors for performance-testing\" test suite or put sesnor UUIDs in ./sensors.json");
        process.exit(1);
    }
    let data = [];
    for (let sensor = 0; sensor < totalSensors; sensor++) {
        let sensorData = {};
        sensorData['sensor_id'] = sensors[sensor];
        sensorData['samples'] = [];
        for (let sample = 0; sample < totalSamples; sample++) {
            let values = {};
            values['time'] = dynamic ? 0 : (new Date()).getTime() / 1000;
            for (let value = 0; value < totalValues; value++) {
                values[`value-${value.toString()}`] = Math.random() * 128;
            }
            sensorData.samples.push(values);
        }
        data.push(sensorData)
    }
    let wrappedData = dynamic ? JSON.stringify({"data": data}).replace(/0,/g, '~tm~,') : JSON.stringify({"data": data});
    await fileSystemHandler.appendDataToFile('./post-data-files/', saveFile, wrappedData);
    return wrappedData;
};

module.exports = {
    formData: formData
};