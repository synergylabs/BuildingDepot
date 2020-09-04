var expect = require('chai').expect,
    supertest = require('supertest'),
    config = require('../config.json'),
    centralApi = supertest(config['centralServiceUri']),
    dataApi = supertest(config['dataServiceUri']),
    data = require('store')

const uuid = require('uuid/v4')

describe('OAuth API should handle ', function () {

    it('invalid client credentials', function (done) {
        centralApi.get('/oauth/access_token/client_id=' + uuid() + '/client_secret=' + uuid())
            .end(function (err, res) {
                // console.log(res.body)
                expect(res.status).to.equal(200)
                expect(res.body).to.have.property('success')
                expect(res.body.success, res.body.error).to.equal('False')
                done()
            })
    })

});