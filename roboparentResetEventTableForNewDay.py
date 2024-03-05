import pythonmysql
import datetime

def main():
  mySQLObject = pythonmysql.PythonMySQL()

  mySQLObject.resetEventTableAndSnooze()

if __name__ == '__main__':
   main()