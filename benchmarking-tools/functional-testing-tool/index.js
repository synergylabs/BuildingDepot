const Mocha = require('mocha'),
    path = require('path');

// Instantiate a Mocha instance.
const mocha = new Mocha();

const glob = require('glob');
const directory = process.argv[2] || './tests';

if (directory.substr(-3) === '.js') {
    mocha.addFile(
        path.resolve(directory)
    );
} else {
    glob.sync(`${directory}/**/*.js`).forEach(function (file) {
        mocha.addFile(
            path.resolve(file)
        );
    });
}

// Run the tests.
mocha.run(function (failures) {
    process.exitCode = failures ? 1 : 0;  // exit with non-zero status if there were failures
});