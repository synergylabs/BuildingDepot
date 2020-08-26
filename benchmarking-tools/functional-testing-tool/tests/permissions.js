var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('./config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('Permission APIs should handle ', function () {

    it('generate an access token', function (done) {
        centralApi.get('/oauth/access_token/client_id='+ config['clientID'] +'/client_secret='+ config['clientSecret'])
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

    it('create a permission with null sg', function (done) {
        data.set('permission', {
            sensor_group: null,
            user_group: 'testing',
            permission: 'rwp'
        })
        centralApi.post('/api/permission')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:data.get('permission')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    it('create a permission with null ug', function (done) {
        data.set('permission', {
            sensor_group: 'testing',
            user_group: null,
            permission: 'rwp'
        })
        centralApi.post('/api/permission')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:data.get('permission')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    it('create a permission with null permission value', function (done) {
        data.set('permission', {
            sensor_group: 'testing',
            user_group: 'testing',
            permission: null
        })
        centralApi.post('/api/permission')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:data.get('permission')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    it('create a permission with invalid permission value', function (done) {
        data.set('permission', {
            sensor_group: 'testing',
            user_group: 'testing',
            permission: uuid()
        })
        centralApi.post('/api/permission')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:data.get('permission')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    it('read an invalid permission', function (done) {
        centralApi.get('/api/permission?user_group=' + null + '&sensor_group=' + null)
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