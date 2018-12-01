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
    results = list(bucket.objects.filter(Prefix='results/illinois-temporal'))
    results = [r.key.replace('results/illinois-temporal/','') for r in results if r.key.endswith('.tgz')]
    processed = list(bucket.objects.filter(Prefix='processed/nyt-annotated-zipped-jsons'))
    processed = [int(p.key.replace('processed/nyt-annotated-zipped-jsons/','').replace('.zip','')) for p in processed if p.key.endswith(".zip")]
    for p in processed:
        if ('%d.ser.tgz' % p) in results and ('%d.timeline.tgz' % p) in results:
            continue
        unfinished.append(p)
    return unfinished