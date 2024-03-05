import time
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client.registry import Collector

import pythonmysql

class CustomCollector(Collector):
    def collect(self):
        self.myDBObject = pythonmysql.PythonMySQL()
        kids = self.myDBObject.getNumKids()
        ROBOPARENT_NUMBER_OF_KIDS_GAUGE = GaugeMetricFamily("ROBOPARENT_NUMBER_OF_KIDS", 'Roboparent Number of Kids', value=kids)
        yield ROBOPARENT_NUMBER_OF_KIDS_GAUGE
        
        requiredRoomStatus = self.myDBObject.getCurrentRequiredRoomStatus()
        ROBOPARENT_REQUIRED_ROOM_STATUS = GaugeMetricFamily("ROBOPARENT_REQUIRED_ROOM_STATUS", 'Roboparent required room status', value=requiredRoomStatus)
        yield ROBOPARENT_REQUIRED_ROOM_STATUS

        ROBOPARENT_ROOM_STATUS_GAUGE = GaugeMetricFamily("ROBOPARENT_ROOM_STATUS", 'Roboparent room status for each kid',labels=['kid'])
        ROBOPARENT_ROOM_COMPLIANCE_GAUGE = GaugeMetricFamily("ROBOPARENT_ROOM_COMPLIANCE", 'Roboparent room compliance for each kid',labels=['kid'])
        #get all kid records so we know what room statuses to query and what metrics to publish
        kidRecords = self.myDBObject.getAllKidRecords()
        for (name) in kidRecords:
            #set room status in the guage
            roomStatus = self.myDBObject.getRoomStatus(name[0])
            ROBOPARENT_ROOM_STATUS_GAUGE.add_metric([name[0]],roomStatus)
            #if the room status is greater than or equal to the required room status, set compliance to 1, if not, set it to 0
            if(roomStatus >= requiredRoomStatus):
                ROBOPARENT_ROOM_COMPLIANCE_GAUGE.add_metric([name[0]],1)
            else:
                ROBOPARENT_ROOM_COMPLIANCE_GAUGE.add_metric([name[0]],0)
        yield ROBOPARENT_ROOM_STATUS_GAUGE
        yield ROBOPARENT_ROOM_COMPLIANCE_GAUGE

if __name__ == '__main__':
    start_http_server(5002)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(30)