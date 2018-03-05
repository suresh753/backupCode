import argparse
import boto3

parser = argparse.ArgumentParser(description='this is a sample program')
group = parser.add_mutually_exclusive_group()
group.add_argument('-e','--environment', metavar='',help='Environment Name')
group.add_argument('-i','--instance', metavar='',help='Instance Id')
args = parser.parse_args()

ec2 = boto3.client('ec2')

custome_instance_id = []

tag_filter = [
            {
                'Name': 'tag-key',
                'Values': [
                    'backup', 'Backup',
                ],
            },
            ]

if args.environment is not None:
    # add filter of
    tag_filter.append(
        {
            'Name': 'tag-value',
            'Values' : [args.environment],

        },

    )
elif args.instance is not None:
    tag_filter = []
    custome_instance_id.append(args.instance)


reservations = ec2.describe_instances(
        Filters=tag_filter,
        InstanceIds=custome_instance_id,
    ).get(
        'Reservations', []
    )

instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

print 'No. of Instances Found are {}'.format(len(instances))
