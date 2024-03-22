from crontab import CronTab
import os

cron = CronTab(user=True)

path = os.path.abspath("./test.py")
job = cron.new(command="python " + "'" + path + "'")
job.minute.every(1) 
job.hour.every(1)   
job.dow.every(1)    

cron.write()
