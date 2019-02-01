import boto.ec2
import time
from s3_util import *
from ec2 import *
def all_have_ip(conn, ids):
    spots = conn.get_all_spot_instance_requests(request_ids=ids)
    for spot in spots:
        if spot.instance_id is None:
            return False
    return True
def get_all_id(conn, ids):
    spots = conn.get_all_spot_instance_requests(request_ids=ids)
    return [spot.instance_id for spot in spots]
def request_spot_instances(count=1,tag='defaultTag',IMAGE_ID="ami-0322f63e84fa693f6",price="0.03",type="one-time",key_name="g0202243",instance_type="t2.large",security_group_ids='sg-47e5fa36'):
    conn = boto.ec2.connect_to_region('us-east-1')
    new_reservation = conn.request_spot_instances(
        price=price,
        image_id=IMAGE_ID,
        count=count,
        type=type,
        key_name=key_name,
        instance_type=instance_type,
        security_group_ids=[security_group_ids])
    time.sleep(5)
    spot_ids = [x.id for x in new_reservation]
    while 1:
        if all_have_ip(conn,spot_ids):
            print "All have ips assigned."
            conn.create_tags(get_all_id(conn,spot_ids),{"Name":tag})
            break;
        print "All don't have ips assigned. Wait for 5 sec..."
        time.sleep(5)
    
    instances = [ins for r in conn.get_all_instances(instance_ids=get_all_id(conn,spot_ids)) for ins in r.instances]
    cache = set()
    while 1:
        allRunning = True
        for ins in instances:
            if ins.ip_address in cache:
                continue
            if ins.state!='running':
                allRunning = False
                print "%s (%s) isn't running." %(ins.ip_address,ins.state)
            else:
                print ins.ip_address+" is running."
                cache.add(ins.ip_address)
        if allRunning:
            print "All are running."
            break
        print "All aren't running. Wait for 10 sec..."
        time.sleep(10)
        instances = [ins for r in conn.get_all_instances(instance_ids=get_all_id(conn,spot_ids)) for ins in r.instances]
    for ins in instances:
        print ins.ip_address
    return new_reservation