let config = require('../config.json'),
    tests = require('../all_tests.json'),
    dataGenerator = require('./dataGenerator'),
    defaults = config.defaults,
    headers = config.headers,
    uri = config.uri;

/**
 * Form options for autocannon test.
 * @return {object} The test options
 */
let formOptions = async function (test) {
    let options = Object.assign({}, defaults);
    let request = test.test === undefined ? Object.assign({}, tests[test.title]) : Object.assign({}, tests[test.test]);
    Object.assign(options, test);
    if (test.duration !== undefined) {
        delete options.amount
    }
    if(await isInvalidUri(options.uri)){
        options.url = uri[request.url];
    }
    if (request.idReplacement !== undefined)
        options['idReplacement'] = request.idReplacement;
    if (options.formData !== undefined) {
        request.body = await dataGenerator.formData(options.formData.saveFile, options.formData.totalSensors, options.formData.totalSamples, options.formData.totalValues, options.formData.dynamic);
        options['totalSensors'] = options.formData.totalSensors;
        options['totalSamples'] = options.formData.totalSamples;
    }
    else if (request.formData !== undefined) {
        request.body = await dataGenerator.formData(request.formData.saveFile, request.formData.totalSensors, request.formData.totalSamples, request.formData.totalValues, request.formData.dynamic);
        options['totalSensors'] = request.formData.totalSensors;
        options['totalSamples'] = request.formData.totalSamples;
    }
    else if (request.file !== undefined) {
        request.body = (test.file === undefined) ? (await fs.readFile(request.file)).toString() : (await fs.readFile(test.file)).toString();
    }
    else if (request.body !== undefined) {
        request.body = (test.body === undefined) ? JSON.stringify(request.body) : JSON.stringify(test.body);
    }
    else if (request.json !== undefined) {
        request.body = (test.json === undefined) ? request.json : test.json;
    }
    if (options.headers === undefined) {
        options['headers'] = headers;
    }
    else {
        Object.assign(options.headers, headers);
    }
    if (test.title !== undefined) {
        options['title'] = test.title;
    }
    options['requests'] = [request];
    if(options.amount !== undefined && options.connections > options.amount){
        console.log("Number of requests can't be less than number of concurrent connections.")
        process.exit(1)
    }
    delete request.idReplacement;
    delete options.body;
    delete request.json;
    delete request.url;
    delete options.json;
    delete request.formData;
    delete options.formData;
    return options
};

/**
 * A function to check if a test exists in the all_tests.json
 * @return {boolean} Returns true if test exists, false otherwise.
 */
let testExists = async function (test) {
    let allTests = Object.keys(tests);
    return (allTests.indexOf(test)>-1)
};

/**
 * A function to check if the uri is valid
 * @return {boolean} Returns true if uri is invalid, false otherwise.
 */
let isInvalidUri = async function (uri) {
    let pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !pattern.test(uri);
};

module.exports = {
    create: formOptions,
    testExists: testExists
};