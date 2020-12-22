var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('./config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('SensorGroup APIs should handle ', function () {

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

    it('create a null sensor_group', function (done) {
        data.set('sensor_group', null)
        centralApi.post('/api/sensor_group')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('sensor_group'),
                    building: data.get('building'),
                    description: 'integration-test'
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

    it('delete an invalid sensorgroup', function (done) {
        centralApi.delete('/api/sensor_group/' + uuid())
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

})