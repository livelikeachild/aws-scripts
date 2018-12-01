import boto.ec2
from paramiko import SSHClient
import paramiko
from termcolor import colored
import boto3
import click
import time
from s3_util import *
from ec2 import *
from spot_instance import *

def partitionsFinished(partitions,cache):
    partitions = partitions.split()
    partitions = [int(x) for x in partitions]
    allFinished = True
    for p in partitions:
        if p in cache:
            continue
        
        if not fileExistsS3('results/illinois-temporal/%d.ser.tgz'%p) or not fileExistsS3('results/illinois-temporal/%d.timeline.tgz'%p):
            print "partition %d unfinished" % p
            allFinished = False
            break
        else:
            print "partition %d finished" %p
            cache.add(p)
    return allFinished
def cplog2s3(ip):
    log_name = 'ip-%s.log' % ip.replace('.','-')
    command = "source ~/.customrc; cptos3.sh ~/log/illinois-temporal/%s logs/illinois-temporal/%s" % (log_name,log_name)
    run_command(host,inline=True,verbose=True,command=command)
    time.sleep(10)
def stopInstanceByIp(ip, dryrun=True):
    conn=boto.ec2.connect_to_region('us-east-1')
    reservations=conn.get_all_instances()
    instances=[i for r in reservations for i in r.instances]
    for ins in instances:
        if ins.ip_address == ip:
            print ins.id+" is stopped now."
            if dryrun:
                continue
            boto.connect_ec2().terminate_instances(ins.id)
def splitPartitions(partitions, n):
    # split partitions into n pieces
    ret = [[]]*n
    i = 0
    for p in partitions:
        ret[i] = ret[i]+[p]
        i+=1
        if i>=n:
            i=0
    ret = [str(x).replace(',','').replace('[','').replace(']','') for x in ret]
    return ret

n = 140
print "#Instances requested: %d" % n
partitions = list_unfinished_partitions()
print "#Partitions unfinished: %d" % len(partitions)
partitions = [x for x in partitions]
print "#Partitions to process: %d" % len(partitions)
partitions = splitPartitions(partitions,n)
print "#Partitions equally assigned to %d instances" % n

tag = 'TimelineLarge2'
forceUpdate = 'false'
MAX_NUM_EVENT = '100'
print "---------------------------"
print "Tag: %s\nforce update: %s\nMAX_NUM_EVENT: %s" %(tag,forceUpdate,MAX_NUM_EVENT)

new_reservation = request_spot_instances(count=n,tag=tag)
tmp = 180
print "Wait for %.2f mins" % (1.0*tmp/60)
time.sleep(tmp)
run_command_all_instances(tag=tag,inline=False,target='./init_script.sh')
time.sleep(30)

ips=get_all_instances(tag)
ips.sort()
command = "./scripts/runIllinoisTemporal.sh "
par2host = {}
for i,host in enumerate(ips):
    print "--------------------"
    print "%d - Executing scripts on %s" %(i,host)
    par2host[partitions[i]] = host
    command_modified = command+"\"%s\" %s %s >> ~/log/illinois-temporal/ip-%s.log &" % (partitions[i], forceUpdate, MAX_NUM_EVENT, host.replace('.','-'))
    run_command(host,command_modified,inline=True,verbose=False)

for key,value in par2host.iteritems():
    print key +"==>"+host

partitions_remaining = partitions
cache = set()
while 1:
    for p_str in partitions_remaining:
        if partitionsFinished(p_str,cache):
            print "%s finished" % p_str
            print "Copy cmd log to s3"
            partitions.remove(p_str)
            host = par2host[p_str]
            cplog2s3(host)
            print "Stop instance"
            stopInstanceByIp(host,dryrun=False)
        else:
            tmp = 60
            print "Wait for %.2f min" % (1.0*tmp/60)
            time.sleep(tmp)
            #time.sleep(5)
    if len(partitions)==0:
        break
    partitions_remaining = partitions
    print "Remaining instances: %d" % len(partitions_remaining)
    print "------------------------"
    for p_str in partitions_remaining:
        print par2host[p_str]

