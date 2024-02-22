var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('./config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('User APIs should handle ', function () {

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

    it('create a user with null email', function (done) {
        data.set('email', null)
        centralApi.post('/api/user')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    first_name: 'Integration',
                    last_name: 'Test',
                    email: data.get('email'),
                    role: 'default'
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


    it('delete an invalid user', function (done) {
        data.set('email', uuid())
        centralApi.delete('/api/user/' + uuid())
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