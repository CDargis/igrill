import falcon
import json
from expiringdict import ExpiringDict

class GrillServer(object):
	def __init__(self):
		self.cache = ExpiringDict(max_len=5000, max_age_seconds=86400)
		self.cache["temps"] = []

	def getData(self):
		return (json.dumps({
			"data": {
				"temps": self.cache.get("temps"),
				"bat": self.cache.get("bat")
			}
		}))

	def handleTemp(self, data):
		temps = self.cache.get("temps")
		time = data[0]["time"]
		exists = False
		for t in temps:
			if t["timestamp"] == time:
				exists = True
		if not exists:
			temps.append(({
				"timestamp": time,
				"measurement": data[0]["fields"]["temperature"]
			}))

	def handleBattery(self, data):
		self.cache["bat"] = data[0]["fields"]["battery_level_percent"]

	def on_get(self, req, resp):
		try:
			resp.status = falcon.HTTP_200
			resp.body = self.getData()
		except Exception as ex:
			resp.status = falcon.HTTP_500
			resp.body = (json.dumps({"exception": ex}))

	def on_post(self, req, resp):
		try:
			body = req.stream.read()
			data = json.loads(body.decode())
			if data[0]["measurement"] == "sensordata":
				self.handleTemp(data)
			if data[0]["measurement"] == "device_battery":
				self.handleBattery(data)
			resp.status = falcon.HTTP_200
			resp.body = (json.dumps({}))
		except Exception as ex:
			resp.status = falcon.HTTP_500
			resp.body = (json.dumps({"exception": ex.message}))

app = falcon.API()

grillServer = GrillServer()

# grillServer will handle all requests to the '/igrill' URL path
app.add_route('/igrill', grillServer)
