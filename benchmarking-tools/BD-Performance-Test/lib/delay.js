/**
 * Delay in ms.
 * @return Promise
 */
function inMilliseconds(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
    inMilliseconds: inMilliseconds
};