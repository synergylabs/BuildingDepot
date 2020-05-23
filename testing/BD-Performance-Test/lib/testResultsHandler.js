let fileSystemHandler = require('./fileSystemHandler'),
    suiteID = new Date().getTime();

/**
 * Handles the result after the test ends
 */
let handleTestResults = async function (res, options) {
    res.requests['average2xx'] = (res.requests.total - res.non2xx) / res.duration;
    res['pointPerSecond'] = res.requests['average2xx'] * options.totalSensors * options.totalSamples;
    console.log('Total Requests: ' + res.requests.total + ' requests\nAverage RPS: ' + res.requests.average2xx + ' req/s\np99 Latency: ' + res.latency.p99 + ' ms\nTotal throughput: ' + res.throughput.total + ' Bytes\nAverage throughput: ' + res.throughput.average + ' Bytes/sec\nConnections: ' + res.connections + '\nDuration: ' + res.duration + ' seconds\nNon-2xx: ' + res.non2xx);
    if(res.pointPerSecond){
        console.log('Sensors: ' + options.totalSensors + '\nSamples: ' + options.totalSamples + '\nEffective points/sec: ' + res.pointPerSecond.toFixed(2) + ' points/sec written');
    }
    console.log('\n\n')
    await saveResult(res);
};

/**
 * Saves result JSON to a file.
 */
let saveResult = async function (result) {
    let testID = new Date().getTime();
    let filename = testID.toString() + ' - ' + result.title + '.json';
    let filePath = './results/' + suiteID + '/';
    await fileSystemHandler.appendDataToFile(filePath, filename, JSON.stringify(result));
};

module.exports = {
    handle: handleTestResults
};