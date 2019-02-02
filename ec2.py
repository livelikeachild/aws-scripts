import boto.ec2
from paramiko import SSHClient
import paramiko
from termcolor import colored

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

def get_all_instances(tag,region="us-east-1"):
    conn=boto.ec2.connect_to_region(region)
    reservations=conn.get_all_instances(filters={"tag:Name":tag})
    instances=[i for r in reservations for i in r.instances]
    print("There're %d instances." % len(instances))
    ret = []
    for i in instances:
        if i.state=='running':
            ret.append(i.ip_address)
    print("%d are running now." % len(ret))
    return ret

def run_command(host, command, user="ubuntu", private_key_file = "/home/qning2/.ssh/g0202243.pem",inline=False,verbose=True):
    if not inline:
        with open(command) as f:
            command = f.read()
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy)
    client.connect(host, username=user, pkey=paramiko.RSAKey.from_private_key_file(private_key_file))
    if inline:
        print "Run command:"+command
    else:
        print "Run command from file: "
        print command
    if verbose:
        stdin, stdout, stderr = client.exec_command(command)
        print stdout.read()
        print colored(stderr.read(), 'red')
    else:
        client.exec_command(command)

def run_command_all_instances(tag,inline=True,target='',dryrun=False,private_key_file="/home/qning2/.ssh/g0202243.pem"):
    if inline==True:
        command = target
    else:
        with open(target) as input_fd:
            command = input_fd.read()
    ips=get_all_instances(tag,region="us-east-1")
    ips.sort()
    for i,host in enumerate(ips):
        print "--------------------"
        print "%d - Executing scripts on %s" %(i,host)
        if dryrun:
            continue
        else:
            run_command(host,command,inline=True,verbose=False, private_key_file=private_key_file)