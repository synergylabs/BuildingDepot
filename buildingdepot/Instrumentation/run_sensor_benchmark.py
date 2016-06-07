# ./ab -p create_sensors.json -T application/json -c 10 -n 10 -H "Authorization:OAuth2 24e4f78e8f08b2d6ad02b46b058d89f2"  http://bdghoses.andrew.cmu.edu:82/api/sensor
import subprocess, requests


sCO = subprocess.check_output
#c = conncurrency level
#n = number of requests
def make_ab_cmd(c=5,n=10):
    return ['./ab',  "-p", "create_sensors.json", "-T", "application/json","-c", str(c), "-n", str(n),'-H', '"Authorization:OAuth2 24e4f78e8f08b2d6ad02b46b058d89f2"', "http://bdghoses.andrew.cmu.edu:82/api/sensor"]

def parseOutput(output):
    ## parses the output of the ab command
    outputList = output.strip().split('\n')
    csvOutput = []
    def getIndexWithStr(k):
        j = filter(lambda x: k in x, outputList)
        try:
            assert(len(j)==1)
        except:
            print 'j:',j
            exit(1)
        return (k,j[0].replace(k,"").strip())
    cleanReqsPerSec = getIndexWithStr("Requests per second:")[1]
    cleanReqsPerSec = cleanReqsPerSec[:cleanReqsPerSec.find('[')].strip()
    csvOutput.extend([getIndexWithStr("Concurrency Level:")[1],
        getIndexWithStr("Complete requests:")[1],
        getIndexWithStr("50%")[1],
        getIndexWithStr("75%")[1],
        getIndexWithStr("90%")[1],
        getIndexWithStr("99%")[1],
        cleanReqsPerSec])
    return ','.join(map(str,csvOutput))

## RUN TESTS FOR DIFFERENT # of requests and concurrency levels

finalOutput = []
for n in [100,500,1000,2500,5000,10000,20000]:
    for c in [1,2,4,8,16]:
        command_joined = ' '.join(make_ab_cmd(c,n))
        finalOutput.append(parseOutput(sCO(command_joined, shell=True)))
        #delete all old sensors made
        requests.get('http://bdghoses.andrew.cmu.edu:8000/api/sensor/deleteall')
print '\n'.join(finalOutput)

