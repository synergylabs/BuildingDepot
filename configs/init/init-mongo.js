db = db.getSiblingDB('admin');
db.auth(process.env.MONGO_INITDB_ROOT_USERNAME, process.env.MONGO_INITDB_ROOT_PASSWORD);

// Single app user in admin so clients can use authSource=admin (mongoengine, pymongo, etc.)
db.createUser({
  user: process.env.MONGO_USERNAME,
  pwd: process.env.MONGO_PASSWORD,
  roles: [
    { role: 'readWrite', db: 'buildingdepot' },
    { role: 'readWrite', db: 'dataservice' },
  ],
});
