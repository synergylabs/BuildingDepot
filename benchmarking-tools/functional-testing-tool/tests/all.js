var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('./config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('An authorized superuser should be able to ', function () {
    this.timeout(10000);
    it('generate an access token', function (done) {
        if (config['clientID'].length && config['clientSecret'].length) {
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
        } else if (config['email'].length && config['password'].length) {
            centralApi.post('/oauth/login')
                .send({
                    data: {
                        email: config['email'],
                        password: config['password']
                    }
                })
                .end(function (err, res) {
                    console.log(res.body)
                    expect(res.status).to.equal(200)
                    expect(res.body).to.have.property('success')
                    expect(res.body).to.have.property('access_token')
                    data.set('authorizedToken', res.body.access_token)
                    expect(res.body.success, res.body.error).to.equal('True')
                    // console.log('Using access token: ' + data.get('authorizedToken'))
                    done()
                })
        } else {
            console.log('No credentials found!')
        }
    })

    it('create a tagtype', function (done) {
        data.set('tagtype', uuid())
        centralApi.post('/api/tagtype')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('tagtype'),
                    description: 'integration-test'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create tagtype: fields', function (done) {
        centralApi.post('/api/tagtype')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: 'fields',
                    description: 'integration-test'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create tagtype: field', function (done) {
        centralApi.post('/api/tagtype')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: 'field',
                    description: 'integration-test'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create tagtype: parent', function (done) {
        centralApi.post('/api/tagtype')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: 'parent',
                    description: 'integration-test'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get a tagtype', function (done) {
        centralApi.get('/api/tagtype/' + data.get('tagtype'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('children')
                expect(res.body).to.have.property('description')
                expect(res.body).to.have.property('name')
                expect(res.body.name).to.equal(data.get('tagtype'))
                expect(res.body).to.have.property('parents')
                done()
            })
    })

    it('create a template', function (done) {
        data.set('template', uuid())
        centralApi.post('/api/template')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('template'),
                    description: 'integration-test',
                    tag_types: [data.get('tagtype'), 'fields', 'field', 'parent']
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get a template', function (done) {
        centralApi.get('/api/template/' + data.get('template'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('description')
                expect(res.body).to.have.property('name')
                expect(res.body.name).to.equal(data.get('template'))
                expect(res.body).to.have.property('tag_types')
                expect(res.body.tag_types).to.include(data.get('tagtype'))
                done()
            })
    })

    it('create a building', function (done) {
        data.set('building', uuid())
        centralApi.post('/api/building')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('building'),
                    description: 'integration-test',
                    template: data.get('template')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get a building', function (done) {
        data.set('sensor_uuid', uuid())
        centralApi.get('/api/building/' + data.get('building'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('description')
                expect(res.body).to.have.property('name')
                expect(res.body.name).to.equal(data.get('building'))
                expect(res.body).to.have.property('template')
                expect(res.body.template).to.equal(data.get('template'))
                done()
            })
    })

    it('create a building tag', function (done) {
        data.set('tag', {
            name: data.get('tagtype'),
            value: '27111995'
        })
        centralApi.post('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: data.get('tag')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create fields building tag', function (done) {
        centralApi.post('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'fields',
                    value: 'fieldA, fieldB'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create fieldA building tag', function (done) {
        centralApi.post('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'field',
                    value: 'fieldA'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create fieldB building tag', function (done) {
        centralApi.post('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'field',
                    value: 'fieldB'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('create parent building tag', function (done) {
        centralApi.post('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'parent',
                    value: data.get('sensor_uuid')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get building tags', function (done) {
        centralApi.get('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('tags')
                expect(res.body.tags[0]).to.contains(data.get('tag'))
                done()
            })
    })

    it('create a dataservice', function (done) {
        data.set('dataservice', uuid())
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
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get a dataservice', function (done) {
        centralApi.get('/api/dataservice/' + data.get('dataservice'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('description')
                expect(res.body).to.have.property('name')
                expect(res.body.name).to.equal(data.get('dataservice'))
                expect(res.body).to.have.property('host')
                expect(res.body).to.have.property('port')
                done()
            })
    })

    it('create a user', function (done) {
        data.set('email', uuid() + '@email.com')
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
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get a user', function (done) {
        centralApi.get('/api/user/' + data.get('email'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('first_name')
                expect(res.body).to.have.property('last_name')
                expect(res.body).to.have.property('email')
                expect(res.body.email).to.equal(data.get('email'))
                expect(res.body).to.have.property('role')
                done()
            })
    })

    it('create a user_group', function (done) {
        data.set('user_group', uuid())
        centralApi.post('/api/user_group')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('user_group'),
                    description: 'integration-test'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('add users to a user_group', function (done) {
        data.set('users',
            [{
                user_id: data.get('email'),
                manager: true
            }])
        centralApi.post('/api/user_group/' + data.get('user_group') + '/users')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    users: data.get('users')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get users from a user_group', function (done) {
        centralApi.get('/api/user_group/' + data.get('user_group') + '/users')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('users')
                expect(res.body.users).to.eql(data.get('users'))
                done()
            })
    })

    it('set admins for a dataservice', function (done) {
        centralApi.post('/api/dataservice/' + data.get('dataservice') + '/admins')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    admins: [data.get('email'), 'admin@buildingdepot.org']
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get admins from a dataservice', function (done) {
        centralApi.get('/api/dataservice/' + data.get('dataservice') + '/admins')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('admins')
                expect(res.body.admins).to.include.members([data.get('email'), 'admin@buildingdepot.org'])
                done()
            })
    })

    it('add buildings to a dataservice', function (done) {
        centralApi.post('/api/dataservice/' + data.get('dataservice') + '/buildings')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    buildings: [data.get('building')]
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get buildings from a dataservice', function (done) {
        centralApi.get('/api/dataservice/' + data.get('dataservice') + '/buildings')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('buildings')
                expect(res.body.buildings).to.include(data.get('building'))
                done()
            })
    })

    it('create a sensor', function (done) {
        data.set('source_name', uuid())
        data.set('source_identifier', uuid())
        data.set('sensor_tags', [data.get('tag')])
        centralApi.post('/api/sensor')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('source_name'),
                    identifier: data.get('source_identifier'),
                    building: data.get('building'),
                    tags: data.get('sensor_tags'),
                    uuid: data.get('sensor_uuid')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('uuid')
                done()
            })
    })

    it('create a sensor_group', function (done) {
        data.set('sensor_group', uuid())
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
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('add tags to a sensor_group', function (done) {
        centralApi.post('/api/sensor_group/' + data.get('sensor_group') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    tags: data.get('sensor_tags')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                // expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('get tags from a sensor_group', function (done) {
        centralApi.get('/api/sensor_group/' + data.get('sensor_group') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('tags_owned')
                expect(res.body.tags_owned).to.deep.include(data.get('tag'))
                done()
            })
    })

    it('create a permission', function (done) {
        data.set('permission', {
            sensor_group: data.get('sensor_group'),
            user_group: data.get('user_group'),
            permission: 'rwp'
        })
        centralApi.post('/api/permission')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: data.get('permission')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('read a permission', function (done) {
        centralApi.get('/api/permission?user_group=' + data.get('user_group') + '&sensor_group=' + data.get('sensor_group'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    sensor_group: data.get('sensor_group'),
                    user_group: data.get('user_group')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('permission')
                expect(res.body.permission).to.equal('r/w/p')
                done()
            })
    })

    it('add tags', function (done) {
        centralApi.post('/api/sensor/' + data.get('sensor_uuid') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    tags: data.get('sensor_tags')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('add view', function (done) {
        data.set('sensor_view', {
            fields: "fieldA, fieldB",
            source_name: "Test View"
        })
        centralApi.post('/api/sensor/' + data.get('sensor_uuid') + '/views')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: data.get('sensor_view')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.set('view_id', res.body.id)
                data.set('sensor_view', Object.assign(data.get('sensor_view'), {'id': res.body.id}))
                done()
            })
    })

    it('get views', function (done) {
        centralApi.get('/api/sensor/' + data.get('sensor_uuid') + '/views')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('views_owned')
                expect(res.body.views_owned).to.eql([data.get('sensor_view')])
                done()
            })
    })

    it('get tags', function (done) {
        centralApi.get('/api/sensor/' + data.get('sensor_uuid') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('tags')
                expect(res.body).to.have.property('tags_owned')
                expect(res.body.tags_owned).to.eql(data.get('sensor_tags'))
                done()
            })
    })

    it('get a sensor', function (done) {
        centralApi.get('/api/sensor/' + data.get('sensor_uuid'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('building')
                expect(res.body.building).to.equal(data.get('building'))
                expect(res.body).to.have.property('name')
                expect(res.body.name).to.equal(data.get('sensor_uuid'))
                expect(res.body).to.have.property('source_identifier')
                expect(res.body.source_identifier).to.equal(data.get('source_identifier'))
                expect(res.body).to.have.property('source_name')
                expect(res.body.source_name).to.equal(data.get('source_name'))
                expect(res.body).to.have.property('metadata')
                expect(res.body).to.have.property('tags')
                expect(res.body.tags).to.eql(data.get('sensor_tags'))
                delete res.body.success
                // Different format for metadata in search sensors
                delete res.body.metadata
                data.set('sensor_object', res.body)
                done()
            })
    })

    it('search sensors', function (done) {
        centralApi.post('/api/sensor/search')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    ID: [data.get('sensor_uuid')],
                    // Building:[data.get('building')],
                    // SourceIdentifier:[data.get('source_identifier')],
                    // SourceName:[data.get('source_name')],
                    // Metadata:data.get('metadata'),
                    // Tags:[data.get('sensor_tags')]
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('result')
                delete res.body.result[0].metadata
                expect(res.body.result).to.deep.include(data.get('sensor_object'))
                done()
            })
    })

    it('register an app', function (done) {
        data.set('app_name', uuid())
        dataApi.post('/api/apps')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('app_name')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('app_id')
                data.set('app_id', res.body.app_id)
                console.log(res.body.app_id)
                done()
            })
    })

    it('get all apps', function (done) {
        data.set('app', {
            name: data.get('app_name'),
            value: data.get('app_id')
        })
        dataApi.get('/api/apps')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('app_list')
                done()
            })
    })

    it('subscribe to a sensor', function (done) {
        dataApi.post('/api/apps/subscription')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    app: data.get('app_id'),
                    sensor: data.get('sensor_uuid')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('subscribe to a view', function (done) {
        dataApi.post('/api/apps/subscription')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    app: data.get('app_id'),
                    sensor: data.get('view_id')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('post time-series data', function (done) {
        var time = new Date().getTime() / 1000
        dataApi.post('/api/sensor/timeseries')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: [{
                    sensor_id: data.get('sensor_uuid'),
                    samples: [
                        {value: 24.56, time: time},
                        {value: Math.random() * 100, time: time}
                    ]
                }]
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('post time-series data (cached permission)', function (done) {
        var time = new Date().getTime() / 1000
        dataApi.post('/api/sensor/timeseries')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: [{
                    sensor_id: data.get('sensor_uuid'),
                    samples: [
                        {value: 24.56, time: time},
                        {value: Math.random() * 100, time: time}
                    ]
                }]
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('read time-series data', function (done) {
        var time = new Date().getTime() / 1000
        dataApi.get('/api/sensor/' + data.get('sensor_uuid') + '/timeseries?start_time=0&end_time=5000000000')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(JSON.stringify(res.body))
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('unsubscribe to a view', function (done) {
        dataApi.delete('/api/apps/subscription')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    app: data.get('app_id'),
                    sensor: data.get('view_id')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('unsubscribe to a sensor', function (done) {
        dataApi.delete('/api/apps/subscription')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    app: data.get('app_id'),
                    sensor: data.get('sensor_uuid')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('delete an app', function (done) {
        dataApi.delete('/api/apps')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    name: data.get('app_name')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('app_id')
                done()
            })
    })

    it('delete a permission', function (done) {
        centralApi.delete('/api/permission?user_group=' + data.get('user_group') + '&sensor_group=' + data.get('sensor_group'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    sensor_group: data.get('sensor_group'),
                    user_group: data.get('user_group')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('permission')
                done()
            })
    })

    it('delete a sensor_group', function (done) {
        centralApi.delete('/api/sensor_group/' + data.get('sensor_group'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('sensor_group')
                done()
            })
    })

    it('delete view', function (done) {
        centralApi.delete('/api/sensor/' + data.get('sensor_uuid') + '/views/' + data.get('view_id'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
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

    it('delete buildings from a dataservice', function (done) {
        centralApi.delete('/api/dataservice/' + data.get('dataservice') + '/buildings')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    buildings: [data.get('building')]
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('delete admins from a dataservice', function (done) {
        centralApi.delete('/api/dataservice/' + data.get('dataservice') + '/admins')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .send({
                data: {
                    admins: [data.get('email'), 'admin@buildingdepot.org']
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                done()
            })
    })

    it('delete a user_group', function (done) {
        centralApi.delete('/api/user_group/' + data.get('user_group'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('user_group')
                done()
            })
    })

    it('delete a user', function (done) {
        centralApi.delete('/api/user/' + data.get('email'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('user')
                done()
            })
    })

    it('delete a dataservice', function (done) {
        centralApi.delete('/api/dataservice/' + data.get('dataservice'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('dataservice')
                done()
            })
    })

    it('get building tags', function (done) {
        centralApi.get('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                expect(res.body).to.have.property('tags')
                expect(res.body.tags[0]).to.contains(data.get('tag'))
                done()
            })
    })

    it('delete a building tag', function (done) {
        centralApi.delete('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: data.get('tag')
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('tag')
                done()
            })
    })

    it('delete parent building tag', function (done) {
        centralApi.delete('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'parent',
                    value: data.get('sensor_uuid')
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('tag')
                data.remove('sensor_uuid')
                done()
            })
    })

    it('delete fields building tag', function (done) {
        centralApi.delete('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'fields',
                    value: 'fieldA, fieldB'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('tag')
                done()
            })
    })

    it('delete fieldA building tag', function (done) {
        centralApi.delete('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'field',
                    value: 'fieldA'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('tag')
                done()
            })
    })

    it('delete fieldB building tag', function (done) {
        centralApi.delete('/api/building/' + data.get('building') + '/tags')
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .expect(200)
            .send({
                data: {
                    name: 'field',
                    value: 'fieldB'
                }
            })
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('tag')
                done()
            })
    })

    it('delete a building', function (done) {
        centralApi.delete('/api/building/' + data.get('building'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('building')
                done()
            })
    })

    it('delete a template', function (done) {
        centralApi.delete('/api/template/' + data.get('template'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('template')
                done()
            })
    })

    it('delete a tagtype', function (done) {
        centralApi.delete('/api/tagtype/' + data.get('tagtype'))
            .set('Authorization', 'Bearer ' + data.get('authorizedToken'))
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('True')
                data.remove('tagtype')
                done()
            })
    })
})

after(function () {
    console.log('\n\t' + data.get('authorizedToken'))
    // cleanUp()
    // printResidue()
})

function cleanUp() {
    data.remove('authorizedToken')
    data.remove('app_name')
    data.remove('app')
    data.remove('source_name')
    data.remove('sensor_id')
    data.remove('source_identifier')
    data.remove('sensor_object')
    data.remove('metadata')
    data.remove('sensor_tags')
    data.remove('buildings')
    data.remove('users')
    data.remove('user_id')
    data.remove('email')
}

function printResidue() {
    var residue = {}
    data.each(function (value, key) {
        residue[key] = value
    })
    if (Object.keys(residue).length > 0) {
        console.log('\n\nSorry! You might have to manually clean up my mess: \n\n')
        console.log(residue)
    }
}
