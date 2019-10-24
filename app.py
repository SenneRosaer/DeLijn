from flask import Flask
import json
from flask import render_template, jsonify
from flask_restful import Resource, Api
import requests
import datetime

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


class Haltes(Resource):
    def get(self, province, line, richting):
        try:
            conn = http.client.HTTPSConnection('api.delijn.be')
            conn.request("GET",
                         "/DLKernOpenData/v1/beta/lijnen/" + province + "/" + line + "/lijnrichtingen/" + richting + "/haltes?%s" % params,
                         "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()

            haltes = json.loads(data)

            returndata = []
            for halte in haltes["haltes"]:
                coor = halte["geoCoordinaat"]

                returndata.append({"lat": coor["latitude"], "long": coor["longitude"],"omschrijving" : halte["omschrijving"]})

            return jsonify({"haltes": returndata})
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))


class Route(Resource):
    def get(self, province, line, richting):
        try:
            conn = http.client.HTTPSConnection('api.delijn.be')
            conn.request("GET",
                         "/DLKernOpenData/v1/beta/lijnen/" + province + "/" + line + "/lijnrichtingen/" + richting + "/dienstregelingen?%s" % params,
                         "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()

            regeling = json.loads(data)
            temp = regeling["ritDoorkomsten"][0]
            temp2 = temp["doorkomsten"]
            returndata = []
            haltes = []

            for item in temp2:
                haltes.append(item["haltenummer"])

            conn = http.client.HTTPSConnection('api.delijn.be')
            conn.request("GET",
                         "/DLKernOpenData/v1/beta/lijnen/" + province + "/" + line + "/lijnrichtingen/" + richting + "/haltes?%s" % params,
                         "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()

            haltesCor = json.loads(data)

            for firstHalte in haltes:
                for secondHalte in haltesCor["haltes"]:
                    if firstHalte == secondHalte["haltenummer"]:
                        returndata.append({"lat": secondHalte["geoCoordinaat"]["latitude"],
                                           "long": secondHalte["geoCoordinaat"]["longitude"]})

            return jsonify({"haltes": returndata})
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))


class Bus(Resource):
    def __init__(self, route=[]):
        self.route = route
        self.waypoints = []

    def calctime(self, stringinput):
        fullstring = stringinput.split("T")
        date = fullstring[0].split("-")
        time = fullstring[1].split(":")
        returnval = datetime.datetime(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]),
                                      int(time[2]))
        return returnval

    def get(self, province, line, richting):
        try:

            conn = http.client.HTTPSConnection('api.delijn.be')
            conn.request("GET",
                         "/DLKernOpenData/v1/beta/lijnen/" + province + "/" + line + "/lijnrichtingen/" + richting + "/dienstregelingen?%s" % params,
                         "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()

            fulldata = json.loads(data)

            time = datetime.datetime.now()
            parameters_to_return = []
            for bus in fulldata["ritDoorkomsten"]:
                number = bus["ritnummer"]
                firstbus = True
                stop_before = 0
                stop_after = 0

                stop_before_time = None
                stop_after_time = None

                last = 0

                for i in range(0, len(bus["doorkomsten"])):
                    halte = bus["doorkomsten"][i]

                    if "dienstregelingTijdstip" not in halte:
                        continue
                    stop_time = self.calctime(halte["dienstregelingTijdstip"])
                    last = i
                    if firstbus is True and time < stop_time:
                        break
                    if time > stop_time:
                        stop_before = i
                        stop_before_time = stop_time
                    else:
                        stop_after = i
                        stop_after_time = stop_time
                        break
                    firstbus = False

                haltenummer1 = bus["doorkomsten"][stop_before]["haltenummer"]
                haltenummer2 = bus["doorkomsten"][stop_after]["haltenummer"]

                if stop_before == last:
                    continue
                if haltenummer1 == haltenummer2:
                    continue

                halte1cor = dict()
                halte2cor = dict()

                conn = http.client.HTTPSConnection('api.delijn.be')
                conn.request("GET",
                             "/DLKernOpenData/v1/beta/lijnen/" + province + "/" + line + "/lijnrichtingen/" + richting + "/haltes?%s" % params,
                             "{body}", headers)
                response = conn.getresponse()
                haltes_data = response.read()
                conn.close()
                haltes_data_parsed = json.loads(haltes_data)

                for halte in haltes_data_parsed["haltes"]:
                    if halte["haltenummer"] == haltenummer1:
                        halte1cor = halte["geoCoordinaat"]
                    if halte["haltenummer"] == haltenummer2:
                        halte2cor = halte["geoCoordinaat"]

                # direct request als eerst met conn niet werk
                url = "https://api.tomtom.com/routing/1/calculateRoute/" + str(halte1cor["latitude"]) + "," + str(
                    halte1cor["longitude"]) + ":" + str(halte2cor["latitude"]) + "," + str(
                    halte2cor["longitude"]) + "/json?traffic=false&key=Tc8Mg2LWtRsRrx4W3YJ1jUcaPr9ylGpF"
                testdata = requests.get(url).text
                print('before?')
                testdata2 = json.loads(testdata)
                print('after!')
                routepoints = testdata2['routes'][0]['legs'][0]['points']

                traveltimebetween = (stop_after_time - stop_before_time).total_seconds()
                traveltimedone = (time - stop_before_time).total_seconds()

                verhouding1 = traveltimedone / traveltimebetween
                verhouding2 = int(len(routepoints) * verhouding1)

                # verhouding nemen van hoeveel procent van de tijd zitten we al
                # dezelfde verhouding nemen op de punten

                parameters_to_return.append(
                    {"lat": routepoints[verhouding2]["latitude"], "lng": routepoints[verhouding2]["longitude"]})
            return {'all_buses': parameters_to_return}
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))


api.add_resource(Haltes, '/haltes/<province>/<line>/<richting>')
api.add_resource(Route, '/route/<province>/<line>/<richting>')
api.add_resource(Bus, '/bus/<province>/<line>/<richting>')

if __name__ == "__main__":
    app.run(debug=True)
    # map met leaflets
    # axios voor  https request
