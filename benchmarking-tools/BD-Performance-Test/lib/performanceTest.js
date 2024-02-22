let createSensors = require('./createSensors'),
    testOptions = require('./testOptions'),
    delay = require('./delay'),
    oAuthHandler = require('./oAuthHandler'),
    testResultsHandler = require("./testResultsHandler"),
    autocannon = require('autocannon'),
    config = require('../config.json');

process.setMaxListeners(0);

/**
 * Add test suite.
 */
let addTestSuite = async function (testSuite) {
    let updateInterval = await oAuthHandler.handle();
    if (testSuite.delay !== undefined) {
        await delay.inMilliseconds(testSuite.delay)
    } else if (config.defaults.delay !== undefined) {
        await delay.inMilliseconds(config.defaults.delay)
    }
    for (let test of testSuite.tests) {
        if (test.test === undefined) {
            test["test"] = testSuite.test;
        }
        let options = await testOptions.create(test);
        if (test.test === "create sensors for performance-testing") {
            await createSensors.runTest(options);
        } else {
            await runTest(options);
        }
    }
    clearInterval(updateInterval)
};


/**
 * Create test suite.
 */
let createTestSuite = async function (test) {
    if (await testOptions.testExists(test)) {
        return {
            title: test,
            tests: [{
                title: test
            }]
        }
    } else {
        console.log('Invalid testSuite or test!');
        process.exit(1);
    }

};

/**
 * Run the tests.
 */
let runTest = async function (options) {
    return new Promise(resolve => {
        let finishedBench = async function (err, res) {
            if (res) {
                await testResultsHandler.handle(res, options);
                resolve(true)
            }
        };
        if (options.title === undefined) {
            options.title = options.test;
        }
        console.log('\nTitle: ' + options.title + '\n'.padEnd(options.title.length + 8, '#'));
        let instance = autocannon(options, finishedBench);
        autocannon.track(instance)
    })
};

module.exports = {
    addTestSuite: addTestSuite,
    createTestSuite: createTestSuite
};