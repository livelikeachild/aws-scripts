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
import sys

class partition_monitor:
    def __init__(self,par_input_s3_dir,par_output_s3_dir,par_input_suffix,par_output_suffix,verbose=True,debug=False):
        # dir should end with "/"
        # suffix doesn't come with a leading "."
        self.par_input_s3_dir = par_input_s3_dir
        self.par_output_s3_dir = par_output_s3_dir
        if not self.par_input_s3_dir.endswith("/"):
            self.par_input_s3_dir += "/"
        if not self.par_output_s3_dir.endswith("/"):
            self.par_output_s3_dir += "/"
        self.par_output_s3_checker = Check_Exist_S3('cogcomp-public-data',self.par_output_s3_dir)

        self.par_input_suffix = par_input_suffix # single suffix
        self.par_output_suffix = par_output_suffix # mulitple suffixes as a list

        bucket = boto3.resource('s3').Bucket('cogcomp-public-data')
        input_all = list(bucket.objects.filter(Prefix=self.par_input_s3_dir))
        self.par_all = [int(p.key.replace(self.par_input_s3_dir,'').replace("."+self.par_input_suffix,'')) for p in input_all if p.key.endswith("."+self.par_input_suffix)]

        self.par_finished = set()
        self.par_unfinished = set()
        if debug:
            self.par_all = self.par_all[:5]
        for p in self.par_all:
            if verbose:
                print "Checking partition %d" % p
            if self.isPartitionFinished(p):
                self.par_finished.add(p)
                if verbose:
                    print "already finished."
            else:
                self.par_unfinished.add(p)
                if verbose:
                    print "Not finished."

    def isPartitionFinished(self,par):
        if par in self.par_finished:
            return True
        for suffix in self.par_output_suffix:
            if not self.par_output_s3_checker.fileExistsS3("%d.%s" %(par,suffix)):
                return False
        self.par_finished.add(par)
        if par in self.par_unfinished:
            self.par_unfinished.remove(par)
        return True

    def arePartitionsFinished(self,partitions):
        # partitions should be a list of integers

        # partitions = "1 2 3", i.e., strings separated by spaces
        # partitions = partitions.split()
        # partitions = [int(x) for x in partitions]
        allFinished = True
        for p in partitions:
            if p in self.par_finished:
                continue
            if not self.isPartitionFinished(p):
                print "partition %d unfinished" % p
                allFinished = False
                break
            else:
                print "partition %d finished" % p
        return allFinished

# def isPartitionFinished(par):
#     return fileExistsS3('results/illinois-temporal-postprocessing/%d.temprel.tgz'%par) and fileExistsS3('results/illinois-temporal-postprocessing/%d.stats'%par)

# def partitionsFinished(partitions,cache):
#     partitions = partitions.split()
#     partitions = [int(x) for x in partitions]
#     allFinished = True
#     for p in partitions:
#         if p in cache:
#             continue
#         if not isPartitionFinished(p):
#             print "partition %d unfinished" % p
#             allFinished = False
#             break
#         else:
#             print "partition %d finished" %p
#             cache.add(p)
#     return allFinished

# def list_unfinished_partitions():
#     unfinished = []
#     s3 = boto3.resource('s3')
#     bucket = s3.Bucket('cogcomp-public-data')
#     results = list(bucket.objects.filter(Prefix='results/illinois-temporal-postprocessing'))
#     results = [r.key.replace('results/illinois-temporal-postprocessing/','') for r in results]
#     processed = list(bucket.objects.filter(Prefix='results/illinois-temporal'))
#     processed = [int(p.key.replace('results/illinois-temporal/','').replace('.ser.tgz','')) for p in processed if p.key.endswith(".ser.tgz")]
#     for p in processed:
#         if ('%d.temprel.tgz' % p) in results and ('%d.stats' % p) in results:
#             continue
#         unfinished.append(p)
#     return unfinished


def cplog2s3(ip,s3logdir,private_key_file):
    log_name = 'ip-%s.log' % ip.replace('.','-')
    command = "source ~/.customrc; cptos3.sh ~/log/%s %s/%s" % (log_name,s3logdir,log_name)
    run_command(ip,inline=True,verbose=True,command=command,private_key_file=private_key_file)
    time.sleep(10)

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

@click.command()
@click.option("--count",default=1) # number of instances to claim
@click.option("--tag",default="defaultTag") # used by AWS instances
@click.option("--image_id",default="ami-0322f63e84fa693f6")
@click.option("--price",default="0.03")
@click.option("--type",default="one-time")
@click.option("--region",default="us-east-1")
@click.option("--thread",default=1)
@click.option("--key_name",default="g0202243")
@click.option("--private_key_file",default="/home/qning2/.ssh/g0202243.pem")
@click.option("--instance_type",default="t2.large")
@click.option("--security_group_ids",default="sg-47e5fa36")
@click.option("--init_script_path",default="./init_script.sh") # must have no input args
@click.option("--main_script_path",default="./scripts/runIllinoisTemporal.sh") # the 1st arg must be partition numbers; the other args are free and are provided by --main_script_args
@click.option("--main_script_args",default="")
@click.option("--input_s3_dir",default="")
@click.option("--output_s3_dir",default="")
@click.option("--input_suffix",default="")
@click.option("--output_suffix",default="")
@click.option("--s3logdir",default="logs")
@click.option("--update_interval",default=60) # check every 60 seconds to close those instances that have finished
@click.option("--debug",is_flag=True)
def run(count,tag,image_id,price,type,region,thread,key_name,private_key_file,instance_type,security_group_ids,init_script_path,main_script_path,main_script_args,input_s3_dir,output_s3_dir,input_suffix,output_suffix,s3logdir,update_interval,debug):
    # myMonitor = partition_monitor('results/illinois-temporal','results/illinois-temporal-postprocessing','ser.tgz',['temprel.tgz','stats'])
    myMonitor = partition_monitor(input_s3_dir, output_s3_dir, input_suffix,
                                  output_suffix.split(),debug=debug)

    print "#Instances requested: %d" % count
    partitions = myMonitor.par_unfinished
    print "#Partitions unfinished: %d" % len(partitions)
    partitions = [x for x in partitions]
    print "#Partitions to process: %d" % len(partitions)
    partitions = splitPartitions(partitions, count*thread)
    print "#Partitions equally assigned to %d instances and %d threads" % (count,thread)

    print "---------------------------"
    print "Tag: %s\nInput arguments: %s" % (tag, main_script_args)
    new_reservation = request_spot_instances(count=count, tag=tag,IMAGE_ID=image_id,price=price,type=type,key_name=key_name,instance_type=instance_type,security_group_ids=security_group_ids,region=region)
    tmp = 120
    print "Wait for %.2f mins to get all spot instances ready" % (1.0 * tmp / 60)
    time.sleep(tmp)
    while True:
        try:
            run_command_all_instances(tag=tag,region=region, inline=False, target=init_script_path,private_key_file=private_key_file)
            break
        except:
            print "Error occurred:", sys.exc_info()[0]
            time.sleep(30)
    print
    time.sleep(120)
    sys.stdout.flush()

    ips = get_all_instances(tag,region=region)
    ips.sort()
    command = main_script_path+" "
    par2host = {}
    for i, host in enumerate(ips):
        print "--------------------"
        print "%d - Executing scripts on %s" % (i, host)
        tmp = ""
        for j in range(thread):
            print "Thread: %d" % j
            tmp += " "+partitions[(i-1)*thread+j]
            command_modified = command + "\"%s\" " % partitions[(i-1)*thread+j]
            command_modified += "%s " % main_script_args
            command_modified += ">> ~/log/ip-%s-%d.log" % (host.replace('.', '-'),j)  # log of the main_script
            run_command(host, command_modified, inline=True, verbose=False, private_key_file=private_key_file)

        par2host[tmp] = host
        # command_modified = command + "\"%s\" %s %s >> ~/log/illinois-temporal/ip-%s.log &" % (
        # partitions[i], forceUpdate, MAX_NUM_EVENT, host.replace('.', '-'))
        # command_modified = command + "\"%s\" " % partitions[i]
        # command_modified += "%s " % main_script_args
        # command_modified += ">> ~/log/ip-%s.log" % host.replace('.', '-') # log of the main_script
        # run_command(host, command_modified, inline=True, verbose=False, private_key_file=private_key_file)

    for key, value in par2host.iteritems():
        print key + "==>" + value
    sys.stdout.flush()

    if not debug:
        partitions_remaining = partitions
        while 1:
            myMonitor.par_output_s3_checker.update()
            for p_str in partitions_remaining:
                p = p_str.split()
                p = [int(x) for x in p]
                if myMonitor.arePartitionsFinished(p):
                    print "%s finished" % p_str
                    print "Copy cmd log to s3"
                    partitions.remove(p_str)
                    host = par2host[p_str]
                    cplog2s3(host,s3logdir,private_key_file=private_key_file)
                    print "Stop instance"
                    stopInstanceByIp(host, dryrun=False, region=region)
                else:
                    tmp = update_interval
                    print "Wait for %.2f min" % (1.0 * tmp / 60)
                    time.sleep(tmp)
                    # time.sleep(5)
            if len(partitions) == 0:
                break
            partitions_remaining = partitions
            print "Remaining instances: %d" % len(partitions_remaining)
            print "------------------------"
            for p_str in partitions_remaining:
                print par2host[p_str]
    else:
        print("In debug mode, instances are not terminated. Please make sure to terminate them manually.")

if __name__ == "__main__":
    run()
