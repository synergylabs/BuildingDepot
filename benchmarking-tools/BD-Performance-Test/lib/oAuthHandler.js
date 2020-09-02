let config = require('../config.json'),
    uri = config.uri,
    headers = config.headers,
    credentials = config.credentials,
    fetch = require('node-fetch'),
    renewHeaderInterval = 86400;

/**
 * Get the new headers.
 * @return {object} The new headers
 */
let getNewHeaders = async function () {
    if (credentials.clientId === "" || credentials.clientSecret === "") {
        console.log("Empty client credentials found in config.json.");
        process.exit(1)
    }
    let getTokenUri = uri.cs + '/oauth/access_token/client_id=' + credentials.clientId + '/client_secret=' + credentials.clientSecret;
    let data = await getData(getTokenUri);
    let newHeaders = {Authorization: 'Bearer ' + data.access_token};
    let expires_in = data.expires_in;
    renewHeaderInterval = 1000 * expires_in - 5000;
    return newHeaders
};

/**
 * Update the headers.
 */
let updateHeaders = function (newHeaders) {
    Object.assign(headers, newHeaders)
};


/**
 * Fetch OAuth response.
 */
let getData = async url => {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.log(error)
    }
};

/**
 * Function to run before the tests.
 * @return {interval} The interval
 */
let handleOAuth = async function () {
    if (config.defaults.oauth !== undefined && config.defaults.oauth) {
        updateHeaders(await getNewHeaders());
        return setInterval(updateHeaders.bind(null, await getNewHeaders()), renewHeaderInterval)
    }
};

module.exports = {
    handle: handleOAuth
};