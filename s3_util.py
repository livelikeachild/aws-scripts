import boto.ec2
import boto3

def fileExistsS3(filepath):
    s3=boto3.resource('s3')
    bucket=s3.Bucket('cogcomp-public-data')
    obj=list(bucket.objects.filter(Prefix=filepath))
    if len(obj)>0 and obj[0].key==filepath:
        return True
    return False