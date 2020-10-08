#==============================================================================
# script to remove the older ami backup based on the retention period defined
# Owner: Arpit Gupta
#==============================================================================

import boto3
import datetime
import os
import time

accountNumber = os.environ['AWS_ACCOUNT_NUMBER']

ec = boto3.client('ec2', 'ap-southeast-1')
#main function to be called
def lambda_handler(event, context):

    imagesResponse = ec.describe_images(
        DryRun=False,
        Owners=[accountNumber],
        Filters=[
            {'Name': 'tag:Backup', 'Values': ['True']}
        ]
    ).get(
        'Images', []
    )

    amiList = []
    currentDate = datetime.datetime.now().strftime('%m-%d-%Y-%H:%M:%S')
    time.sleep(10)
    for image in imagesResponse:
        deleteOn = ''
        for tag in image['Tags']:
            if tag['Key'] == 'DeleteOn':
                deleteOn = tag['Value']
                break
        if deleteOn == '':
            continue
        if deleteOn <= currentDate:
            print("Cleaning up AMI {}".format(image['ImageId']))
            ec.deregister_image(
                DryRun=False,
                ImageId=image['ImageId']
            )
            amiList.append(image['ImageId'])
            snapshots = ec.describe_snapshots(
                DryRun=False,
                OwnerIds=[
                    accountNumber
                ],
                Filters=[
                    {
                        'Name': 'description',
                        'Values': [
                            '*'+image['ImageId']+'*'
                        ]
                    }
                ]
            ).get(
                'Snapshots', []
            )
            for snapshot in snapshots:
                print(">>Cleaning up Snapshot{}".format(snapshot['SnapshotId']))
                time.sleep(5)
                ec.delete_snapshot(
                    DryRun = False,
                    SnapshotId = snapshot['SnapshotId']
                )
        else:
            print("{} not yet scheduled for cleanup".format(image['ImageId']))
    print("*******************************")
    if len(amiList)==0:
        print("No AMIs were deleted")
    else:
        print("{} AMIs were deleted\nDeleted the following:".format(len(amiList)))
        for ami in amiList:
            print(ami)