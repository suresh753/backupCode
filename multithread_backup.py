import boto3
from Queue import Queue
from threading import Thread

ec = boto3.client('ec2')
q = Queue(maxsize=0) #initializing queue to infinate values

def backup_task(instace_id):
	#back up code here
	print instace_id
	
	
	
def worker():
	# this worker function assign every instance to each worker thread 
	while True:
		Instance_id = q.get()
		backup_task(Instance_id)
		q.task_done()

reservations = ec.describe_instances(
        
    ).get(
        'Reservations', []
    )
 
instances = sum(
        [
            [q.put(i['InstanceId']) for i in r['Instances']]   #adding instace id to queue
            for r in reservations
        ], [])
 
print "Found %d instances that need backing up" % len(instances)
  
 #creating thread for each instance id
for i in range(len(instances)):
	t=Thread(target=worker)
	t.setDaemon(True)
	t.start()


q.join() #wait for all threads to complete
 
 

