'use strict';
let config = require('./config.json'),
    run = require('./lib/performanceTest'),
    fileSystemHandler = require("./lib/fileSystemHandler"),
    testSuite;

if (process.argv[2] === undefined) {
    testSuite = config.testSuite;
}
else {
    testSuite = process.argv[2];
}

let runTestSuite = async function(testSuite){
    if(await fileSystemHandler.exists(testSuite)){
        let testSuiteJSON = (await fileSystemHandler.readFile(testSuite)).toString();
        run.addTestSuite(JSON.parse(testSuiteJSON));
    }
    else{
        run.addTestSuite(await run.createTestSuite(testSuite));
    }
};

runTestSuite(testSuite);