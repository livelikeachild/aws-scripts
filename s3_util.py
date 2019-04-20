import boto.ec2
import boto3
class Check_Exist_S3:
    def __init__(self,bucket,path):
        self.bucket = boto3.resource('s3').Bucket(bucket)
        if not path.endswith('/'):
            path = path+"/"
        self.path = path
        self.obj = list(self.bucket.objects.filter(Prefix=self.path))
    def update(self):
        self.obj = list(self.bucket.objects.filter(Prefix=self.path))
    def fileExistsS3(self,filename):
        for file in self.obj:
            if file.key == self.path+filename:
                return True
        return False

# def fileExistsS3(filepath):
#     s3=boto3.resource('s3')
#     bucket=s3.Bucket('cogcomp-public-data')
#     obj=list(bucket.objects.filter(Prefix=filepath))
#     if len(obj)>0 and obj[0].key==filepath:
#         return True
#     return False