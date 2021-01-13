var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('./config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('Firebase Notifications APIs should handle ', function () {

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

    // it('create a user', function (done) {
    //     data.set('email', uuid() + '@email.com')
    //     centralApi.post('/api/user')
    //         .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
    //         .send({
    //             data: {
    //                 first_name: 'Integration',
    //                 last_name: 'Test',
    //                 email: data.get('email'),
    //                 role: 'default'
    //             }
    //         })
    //         .end(function (err, res) {
    //             // console.log(res.body)
    //             expect(res.status).to.equal(200)
    //             expect(res.body).to.have.property('success')
    //             expect(res.body.success, res.body.error).to.equal('True')
    //             done()
    //         })
    // })

    it('create a sensor on null building', function (done) {
        data.set('source_name', null)
        data.set('source_identifier', null)
        data.set('sensor_uuid', uuid())
        centralApi.post('/api/sensor')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:{
                    name: data.get('source_name'),
                    identifier: data.get('source_identifier'),
                    building: null,
                    uuid: data.get('sensor_uuid')
                }
            })
            .end(function (err, res) {
                console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    //GET notificationID
    it('create a notificationID for an user', function (done) {
        data.set('notificationID', {
            id: config['clientID'] //firebase token or rabbitMQ queue name
        })
        centralApi.post('/api/notification/id')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:data.get('notificationID')
            })
            .end(function (err, res) {
                console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    // POST permission request to a sensor uuid
    it('create a permission notification request ', function (done) {
        data.set('permissionNotificationRequest', {
            target_sensors : data.get('sensor_uuid'),
            timestamp: new Date().getTime() / 1000
        })
        centralApi.post('/api/permission/request')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data:data.get('permissionNotificationRequest')
            })
            .end(function (err, res) {
                console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })
    //
    // //GET Firebase Notification
    //
    //GET permission historical requests of sensor uuid
    it('read historical permission notification', function (done) {
        centralApi.get('/api/permission/request?timestamp=' + (new Date().getTime() - (5 * 60 * 1000)  / 1000))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

    it('delete a sensor', function (done) {
        centralApi.delete('/api/sensor/' + data.get('sensor_uuid'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

});

