`examples/connectDB.py`: Demo code to select/insert/delete triples using the sparqlWrapper package as database user dba.
Also contains examples to create a graph with a turtle file's URI, create a graph using RDF's graph object and
delete a graph.  Tested against Virtuoso 7.2 and 7.2.5.

`graph_db_wrapper/brickEndpoint.py`: Class for basic operations against a graph database.  Tested against Virtuoso 7.2 and 7.2.5.  Usage examples can be found in `tests/test_BrickEndpoint.py'.

**Note**: With blank nodes (BNode) in the graph parsed from a .ttl file,
the database side loading method (LOAD INTO) should be used.
That is because the database makes no guarantee that the BNode names are kept consistent across multiple
INSERT queries.
When the file is large, even if the caller of SPARQLWrapper inserts all triples with one query SPARQLWrapper may
still divide the inserts into batches and thus break the BNode name consistency.

**Build and install Virtuoso 7.2.5:**
```
sudo aptitude install dpkg-dev build-essential
# use a version of libssl-dev in the version range as required by Virtuoso
sudo apt-get install openssl libssl1.0-dev

wget https://sourceforge.net/projects/virtuoso/files/virtuoso/7.2.5/virtuoso-opensource-7.2.5.tar.gz
tar xfzv virtuoso-opensource-7.2.5.tar.gz
cd virtuoso-opensource-7.2.5/
./configure --prefix=/usr/local/
sudo make install

cd /usr/local/var/lib/virtuoso/db
sudo virtuoso-t -fd &
# test server response
curl localhost:8890
```
**Make Virtuoso a service with systemd:**

Stop virtuoso server first.  Create service unit file `/lib/systemd/system/virtuoso.service`:

```
[Unit]
Description=Virtuoso Graph Database
After=network.target
[Service]
ExecStart=/usr/local/bin/virtuoso-t -fd
Restart=always
WorkingDirectory=/usr/local/var/lib/virtuoso/db
[Install]
WantedBy=multi-user.target
```

```
sudo ln -s /lib/systemd/system/virtuoso.service /etc/systemd/system/virtuoso.service 
sudo systemctl start virtuoso
sudo systemctl enable virtuoso
```

**Change default dba user password:**
```
isql -U dba -P dba
SQL>  set password dba yourSecurePassword;
exit;
```

**Use Virtuoso container for quick tests:** See `.travis.yml'.

**Note**: For Virtuoso 6.1, the following permissions are explicitly needed.  Grant them
to `SPARQL` using Virtuoso's web interface `DBhost:8890`.  Unnecessary for Virtuoso 7.2.5.
```
grant execute on "DB.DBA.SPARQL_INSERT_DICT_CONTENT" to "SPARQL";
grant execute on "DB.DBA.SPARQL_DELETE_DICT_CONTENT" to "SPARQL";
grant execute on "DB.DBA.SPARQL_MODIFY_BY_DICT_CONTENTS" to "SPARQL";
grant execute on "DB.DBA.SPARUL_LOAD" to "SPARQL";
```
