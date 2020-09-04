let fs = require('nano-fs');

/**
 * Creates path recursively and appends data to a file.
 */
let appendDataToFile = async function (filePath, saveFile, data) {
    await fs.mkpath(filePath);
    await fs.appendFile(filePath + saveFile, data);
};

/**
 * Creates path recursively and writes data to a file.
 * NOTE: Overwrites data if file exists already.
 */
let writeDataToFile = async function (filePath, saveFile, data) {
    await fs.mkpath(filePath);
    await fs.writeFile(filePath + saveFile, data);
};

/**
 * Returns true if a file exists.
 */
let exists = async function (filePath) {
    return new Promise(resolve => {
        let exists = fs.exists(filePath, (exists) => {
            resolve(exists);
        })
    })
};

/**
 * Returns file data
 */
let readFile = async function (filePath) {
    return fs.readFileSync(filePath);
};

module.exports = {
    appendDataToFile: appendDataToFile,
    writeDataToFile: writeDataToFile,
    exists: exists,
    readFile: readFile
};