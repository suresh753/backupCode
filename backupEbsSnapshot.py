import boto3
import datetime
import time
import botocore

ec2 = boto3.client('ec2')
snap_resource = boto3.resource('ec2')
sns = boto3.client('sns')

volumes_objects = []

class Aws_Instance:

    def __init__(self, ins_name, ins_id, vol_id, vol_label, vol_type, retention_days, env, delete_date):

        # declaring instance attributes

        self.snapshot_id = None
        self.snapshot_state = "InComplete"
        self.instance_name = ins_name
        self.instance_id = ins_id
        self.volume_id = vol_id
        self.volume_label = vol_label
        self.volume_type = vol_type
        self.retention_days = retention_days
        self.env = env
        self.delete_date = delete_date

        max_try = 3;

        print(
        self.snapshot_id, self.snapshot_state, self.instance_name, self.instance_id, self.volume_id, self.volume_label,
        self.volume_type, self.retention_days, self.env, self.delete_date)

        i = 1
        while i <= max_try and self.snapshot_state != 'completed':
            try:
                self.snapshot_id = snap_resource.create_snapshot(VolumeId=self.volume_id).id
                snapshot_object = snap_resource.Snapshot(self.snapshot_id)
                snapshot_object.create_tags(
                    Tags=[
                        {'Key': 'DeleteOn', 'Value': self.delete_date},
                        {'Key': 'Instance_Name', 'Value': self.instance_name},
                        {'Key': 'Instance_id', 'Value': self.instance_id},
                        {'Key': 'Env', 'Value': self.env},
                        {'Key': 'VolumeType', 'Value': self.volume_type},
                        {'Key': 'VolumeLable', 'Value': self.volume_label},
                        {'Key': 'VolumeId', 'Value': self.volume_id},
                    ]
                )

                waiter_for_snapshot_complete = ec2.get_waiter('snapshot_completed')
                waiter_for_snapshot_complete.wait(SnapshotIds=[self.snapshot_id, ])
                self.snapshot_state = snapshot_object.state

            except botocore.exceptions.WaiterError as e:
                i += 1
                print("Error while creating snapshot retrying for {} time and error is : {}").format(i,e)
                self.snapshot_state = 'failure'


def delete_ebs_snapshots():
    snap_del = []
    day = 0  # 0 for today
    delete_date = datetime.date.today() + datetime.timedelta(days=day)
    delete_on = delete_date.strftime('%Y-%m-%d')
    print(delete_on)
    response = ec2.describe_snapshots(
    Filters=[{'Name': 'tag-key', 'Values': ['DeleteOn']}, {'Name': 'tag-value', 'Values': [delete_on]}, ], )
    for j in response["Snapshots"]:
        try:
            snap_id = (j['SnapshotId'])
            snap_del.append(snap_id)
            res = ec2.delete_snapshot(SnapshotId=snap_id, )
            print(snap_id, "Deleted")
            # print(res)
        except:
            print("Error deleting snapshot")
    print("Deleted Snapshots: ", len(snap_del), "\nList :", snap_del)


def main_program():
    reservations = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag-key',
                'Values': [
                    'backup', 'Backup',
                ]
            },
        ],
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print len(instances)

    # log on how many instance discovered

    try:
        for instance in instances:
            retention_days = 60
            environment = ""
            instance_name = ""
            volume_type = ""
            instance_id = instance['InstanceId']  # store instance id
            # store root device vol ex: /dev/sda1
            for tag in instance['Tags']:
                if (tag['Key'] == 'Retention'):
                    retention_days = tag['Value']
                if (tag['Key'] == "Environment"):
                    environment = tag['Value']
                if (tag['Key'] == "Name"):
                    instance_name = tag['Value']

            for vol in instance['BlockDeviceMappings']:
                if vol.get('Ebs', None) is None:
                    continue
                volume_label = (vol['DeviceName'])  # volume mountpoint
                volume_type = 'root'
                if volume_label != instance['RootDeviceName']:
                    volume_type = 'data'
                volume_id = (vol['Ebs']['VolumeId'])
                delete_date = datetime.date.today() + datetime.timedelta(days=int(retention_days))
                delete_fmt = delete_date.strftime('%Y-%m-%d')
                # print instance_name, instance_id, volume_id, volume_label, volume_type, retention_days, environment, delete_date
                create_volume = Aws_Instance(instance_name, instance_id, volume_id, volume_label, volume_type, retention_days,
                                  environment, delete_fmt)
                volumes_objects. append(create_volume)


    except Exception, e:
        print("Error in sending obj=", str(e))


    delete_ebs_snapshots()       # delete ebs snapshots which are 60 days old.
  
    for volume in volumes_objects:             # for every object checking failed snapshot attributes
       if "failure" == volume.snapshot_state:
           print 'Instance Id : {} Volume Id : {}',format(volume.instance_id,volume.volume_id)
    else:
        print 'Snapshots are created Successfully'

main_program()
