var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('./config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('DataService APIs should handle ', function () {

    it('generate an access token', function (done) {
        centralApi.get('/oauth/access_token/client_id=' + config['clientID'] + '/client_secret=' + config['clientSecret'])
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('access_token')
                data.set('authorizedToken', res.body.access_token)
                // console.log('Using access token: ' + data.get('authorizedToken'))
                done()
            })
    })

    it('create a dataservice', function (done) {
        data.set('dataservice', null)
        centralApi.post('/api/dataservice')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('dataservice'),
                    description: 'integration-test',
                    host: '127.0.0.1',
                    port: 83
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

})