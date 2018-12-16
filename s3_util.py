import boto.ec2
import boto3
def fileExistsS3(filepath):
    s3=boto3.resource('s3')
    bucket=s3.Bucket('cogcomp-public-data')
    obj=list(bucket.objects.filter(Prefix=filepath))
    if len(obj)>0 and obj[0].key==filepath:
        return True
    return False
def list_unfinished_partitions():
    unfinished = []
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('cogcomp-public-data')
    results = list(bucket.objects.filter(Prefix='results/illinois-temporal-postprocessing'))
    results = [r.key.replace('results/illinois-temporal-postprocessing/','') for r in results]
    processed = list(bucket.objects.filter(Prefix='results/illinois-temporal'))
    processed = [int(p.key.replace('results/illinois-temporal/','').replace('.ser.tgz','')) for p in processed if p.key.endswith(".ser.tgz")]
    for p in processed:
        if ('%d.temprel.tgz' % p) in results and ('%d.stats' % p) in results:
            continue
        unfinished.append(p)
    return unfinished