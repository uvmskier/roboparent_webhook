import pythonmysql
import datetime
from datetime import datetime, timedelta

def main():
  mySQLObject = pythonmysql.PythonMySQL()

  #requiredRoomStatus = mySQLObject.getCurrentRequiredRoomStatus()

  #print(requiredRoomStatus)

  #cutoffTime = mySQLObject.getCutoffTimeForDay("Monday")
  #currentTime = datetime.strptime("09:30:00", "%H:%M:%S")
  #currentTimeDelta = timedelta(hours=currentTime.hour, minutes=currentTime.minute, seconds=currentTime.second)
 
  #if(currentTimeDelta < cutoffTime):
  #   print("current time is before cutoff")
  #elif(currentTimeDelta > cutoffTime):
  #   print("current time is after cutoff")

  #today = datetime.strftime(datetime.today(),"%A")
  #print(today)

  #mySQLObject.resetEventTable()

  #now = datetime.datetime.now()
  #mySQLObject.insertEvent("Ethan",now, "FailedCleanup")
  #mySQLObject.insertEvent("Benjamin",now, "SuccessfulCleanup")

  roomStatus1 = mySQLObject.getRoomStatus("Ethan")
  #roomStatus2 = mySQLObject.getRoomStatus("Benjamin")
  print(roomStatus1)
  #print(roomStatus2)
    #mySQLObject.printStuff()
    
    #numKids = mySQLObject.getNumKids()
    #print(numKids)
  
  #mySQLObject.setSnooze("Ethan","2024-02-01")
  #mySQLObject.removeSnooze("Ethan")
  #mySQLObject.removeSnoozeAuto("Ethan")
  
  #snoozeStatus = mySQLObject.getSnoozeStatus("Ethan")
  #print(snoozeStatus)
  #mySQLObject.resetEventTableAndSnooze()
  #mySQLObject.removeSnooze("Ethan","uvmskier")
  #snoozeStatus = mySQLObject.getSnoozeStatus("Ethan")
  #print(snoozeStatus)
  #mySQLObject.removeSnooze("Ethan",'automation')
if __name__ == '__main__':
   main()