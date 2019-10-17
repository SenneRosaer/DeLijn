from flask import Flask
import json
from flask import render_template
from flask_restful import Resource,Api

app = Flask(__name__)
api = Api(app)


########### Python 3.2 #############
import http.client, urllib.request, urllib.parse, urllib.error, base64

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'd77e2bb9a0fa410885193ea120120839',
}

params = urllib.parse.urlencode({
    # Request parameters
    'datum': '{string}',
})
#####################################

@app.route('/')
def home():
    return render_template('Home.html')

class HelloWorld(Resource):
    def get(self):
        try:
            conn = http.client.HTTPSConnection('api.delijn.be')
            conn.request("GET",
                         "/DLKernOpenData/v1/beta/entiteiten/1?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            print(data)
            conn.close()
            return json.loads(data)
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))


class Test(Resource):
    def get(self,province, line, richting):
        try:
            conn = http.client.HTTPSConnection('api.delijn.be')
            conn.request("GET", "/DLKernOpenData/v1/beta/lijnen/"+province+"/"+line+"/lijnrichtingen/"+richting+"/dienstregelingen?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            print(data)
            conn.close()
            return json.loads(data)
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))

api.add_resource(HelloWorld, '/')
api.add_resource(Test,'/<province>/<line>/<richting>')



if __name__ == "__main__":
    app.run(debug = True)
    #map met leaflets
    #axios voor  https request


