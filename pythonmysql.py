import mysql.connector
import datetime
from datetime import date, datetime, timedelta

import dotenv, os, socket

class PythonMySQL:

  #constructor
  #precondition:  none
  #postcondition:  database initialized
  def __init__(self):

    if socket.gethostname() == 'nuc1':
      dotenv.load_dotenv('/home/brian/python-scripts/secrets.env')
    else:
      dotenv.load_dotenv('secrets.env')

    self.myDB = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_DATABASE')
    )
  #deconstructor
  #precondition:  object exists
  #postcondition:  database disconnected
  def __del__(self):
     self.myDB.disconnect()
  def printStuff(self):
    print(self.foo)
    print(self.foo2)
  
  #method to insert an event into the db
  def insertEvent(self,kid,created,eventname,slackuser):
    mycursor = self.myDB.cursor()
    sql = "INSERT INTO roboparentevent (kid, created, eventname,slackuser) VALUES (%s,%s,%s,%s)"
    val = (kid,created,eventname,slackuser)
    mycursor.execute(sql,val)
    self.myDB.commit()
    del mycursor
  
  #method to delete all events, insert NewDay events for each kid
  def resetEventTableAndSnooze(self):
    deleteCursor = self.myDB.cursor()
    sql = "delete from roboparentevent"
    deleteCursor.execute(sql)
    self.myDB.commit()
    del deleteCursor

    todayDate = date.today()
    midnightToday = str(todayDate) + " 00:00:00"
    midnightToday1s = str(todayDate) + " 00:00:01"

    kidRecords = self.getAllKidRecords()
    for (name) in kidRecords:
        #use removeSnoozeAuto function on each kid to remove snooze if expired
        self.removeSnoozeAuto(name[0])
        self.insertEvent(name[0],midnightToday,"NewDay","automation")  
        #check to see if kid is currently snoozed, if true, insert the snooze event
        snoozeStatus = self.getSnoozeStatus(name[0])
        if snoozeStatus["snoozeStatus"] == True:
          self.insertEvent(name[0],midnightToday1s,"Snooze","automation")
  
  def removeSnooze(self,kid,slackuser):
    snoozeStatus = self.getSnoozeStatus(kid)
    if (snoozeStatus['snoozeStatus'] == True):
      deleteCursor = self.myDB.cursor(buffered=True)
      sql = "delete from snooze where kid = \"{}\";".format(kid)
      deleteCursor.execute(sql)
      self.myDB.commit()

      current_time = datetime.now()
      self.insertEvent(kid,self.getCurrentTimeStamp(),'Unsnooze',slackuser)

  def getCurrentTimeStamp(self):
    current_time = datetime.now()
    correct_timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    return correct_timestamp

  def removeSnoozeAuto(self,kid):
    snoozeStatus = self.getSnoozeStatus(kid)
    if (snoozeStatus['snoozeStatus'] == True):
      date1 = snoozeStatus['snoozeDate']
      date2 = date.today()
      if(date1 < date2):
        #self.removeSnooze(kid,'automation')
        deleteCursor = self.myDB.cursor(buffered=True)
        sql = "delete from snooze where kid = \"{}\";".format(kid)
        deleteCursor.execute(sql)
        self.myDB.commit()

  #function to return all kid records in kid table
  def getAllKidRecords(self):
    selectCursor = self.myDB.cursor(buffered=True)
    sql = "select name from kid"
    selectCursor.execute(sql)
    return selectCursor
  
  #function to return number of kids
  def getNumKids(self):
    selectCursor = self.myDB.cursor()
    sql = "select count(*) as count from kid"
    selectCursor.execute(sql)
    result = selectCursor.fetchall()
    rowcount = result[0][0]
    return rowcount
  def getRoomStatus(self,kid):
    selectCursor = self.myDB.cursor(buffered=True)
    sql = "select kid, eventname, created from roboparentevent where kid = \"{}\" order by created DESC;".format(kid)
    selectCursor.execute(sql)
    result = selectCursor.fetchone()
    roomStatus = result[1]

    #if the last event is Unsnooze, run the query again to exclude snooze/unsnooze events and get the last event
    if roomStatus == 'Unsnooze':
      sql = "select kid, eventname, created from roboparentevent where kid = \"{}\" and eventname not in (\"Snooze\",\"Unsnooze\") order by created DESC;".format(kid)
      selectCursor.execute(sql)
      result = selectCursor.fetchone()
      roomStatus =result[1]

    if roomStatus == 'NewDay':
      return 0
    elif roomStatus == 'SuccessfulCleanup':
      return 1
    elif roomStatus == 'FailedCleanup':
      return 0
    elif roomStatus == 'DismissedCleanup':
      return 2
    elif roomStatus == 'Snooze':
      return 2
    del selectCursor
  def getCutoffTimeForDay(self,day):
    selectCursor = self.myDB.cursor(buffered=True)
    sql = "select cutofftime from cutofftime where dayName = \"{}\";".format(day)
    selectCursor.execute(sql)
    result = selectCursor.fetchone()
    cutoffTime = result[0]
    return cutoffTime
  def getCurrentRequiredRoomStatus(self):
    selectCursor = self.myDB.cursor(buffered=True)
    cutoffTime = self.getCutoffTimeForDay(datetime.strftime(datetime.today(),"%A"))
    now = datetime.now()
    if(timedelta(hours=now.hour, minutes=now.minute, seconds=now.second) < cutoffTime):
      return 0
    elif(timedelta(hours=now.hour, minutes=now.minute, seconds=now.second) > cutoffTime):
      return 1
  def getSnoozeStatus(self,kid):
    selectCursor = self.myDB.cursor(buffered=True)
    sql = "select kid,snoozedate from snooze where kid = \"{}\";".format(kid)
    selectCursor.execute(sql)
    if selectCursor.rowcount == 0:
      myDict = {"snoozeStatus": False}
      return myDict
    else:
      result = selectCursor.fetchone()
      myDict = {"snoozeStatus": True, "snoozeDate": result[1]}
      return myDict
    del selectCursor
  def setSnooze(self,kid,snoozeDate,slackuser):
    deleteCursor = self.myDB.cursor(buffered=True)
    sql = "delete from snooze where kid = \"{}\";".format(kid)
    deleteCursor.execute(sql)
    self.myDB.commit()

    insertCursor = self.myDB.cursor(buffered=True)
    sql = "insert into snooze (kid,snoozedate) values (\"{}\",\"{}\")".format(kid,snoozeDate)
    insertCursor.execute(sql)
    self.myDB.commit()

    self.insertEvent(kid,self.getCurrentTimeStamp(),'Snooze',slackuser)