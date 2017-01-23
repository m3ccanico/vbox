#!/usr/bin/env python

import argparse
import logging
import sys
import subprocess
import string
import re
import os
import time

VBOX_MANAGE='/usr/local/bin/VBoxManage'
WIRESHARK='/usr/local/bin/wireshark'

def read_parameter(argv):
    
    parser = argparse.ArgumentParser(description='Manages VirtualBox machines')
    parser.add_argument('-d', '--debug', action='store_true', default=False, help='if debugging and info messages should be shown (default=no)')
    parser.add_argument('-n', '--nic', type=int, action='store', default=False, help='the network interface (1=Adapter 1)')
    parser.add_argument('machine', type=str, help='the name of the VM')
    parser.add_argument('action', type=str, help='[start|stop]')
    args = parser.parse_args()
    
    return args


def delete_file(filename):
    os.remove(filename)


def get_vms():
    cmd = [ VBOX_MANAGE, 'list', 'vms' ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (out, err) = p.communicate()
    exit = p.wait
    
    machines = []    
    if p.returncode == 0:
        for line in string.split(out, '\n'):
            m = re.search('"(.*)" {(.*)}', line)
            if m:
                machines.append( {'name': m.group(1), 'uuid': m.group(2)})
    return machines


def vm_save_state(uuid):
    cmd = [ VBOX_MANAGE, 'controlvm', uuid, 'savestate' ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (out, err) = p.communicate()
    exit = p.wait
    if p.returncode == 0:
        time.sleep(1)
        return
    else:
        logging.error('cannot save state of VM %s' % uuid)
        sys.exit(2)


def vm_start_trace(uuid, nic, filename):
    cmd = [ VBOX_MANAGE, 'modifyvm', uuid, '--nictrace%i' % nic, 'on', '--nictracefile%i' % nic, filename ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (out, err) = p.communicate()
    exit = p.wait
    if p.returncode == 0:
        time.sleep(1)
        return
    else:
        logging.error('cannot start trace for VM %s nic:%i filename:%s' % (uuid, nic, filename))
        sys.exit(2)


def vm_stop_trace(uuid, nic):
    cmd = [ VBOX_MANAGE, 'modifyvm', uuid, '--nictrace%i' % nic, 'off' ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (out, err) = p.communicate()
    exit = p.wait
    if p.returncode == 0:
        time.sleep(1)
        return
    else:
        logging.error('cannot stop trace for VM %s nic:%i filename:%s' % (uuid, nic, filename))
        sys.exit(2)


def vm_start(uuid):
    cmd = [ VBOX_MANAGE, 'startvm', uuid ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (out, err) = p.communicate()
    exit = p.wait
    if p.returncode == 0:
        time.sleep(1)
        return
    else:
        logging.error('cannot start VM %s' % uuid)
        sys.exit(2)


def wireshark_start(filename, title):
    cmd = [ WIRESHARK, filename, '-o', 'gui.window_title:%s' % title ]
    subprocess.Popen(cmd)

def main(argv):
    args = read_parameter(argv)
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
        
    uuid = ''
    for machine in get_vms():
        if machine['name'] == args.machine:
            uuid = machine['uuid']
    
    if not uuid:
        logging.error('machine "%s" not found' % args.machine)
        sys.exit(2)
    
    filename = '%s/%s-adp%d.pcap' % (os.path.expanduser('~'), args.machine.replace(' ', ''), args.nic)
    
    if args.action == "start":
        vm_save_state(uuid)
        vm_start_trace(uuid, int(args.nic), filename)
        vm_start(uuid)
        title = '%s nic%s' % (args.machine, args.nic)
        wireshark_start(filename, title)
    elif args.action == "stop":
        vm_save_state(uuid)
        vm_stop_trace(uuid, args.nic)
        delete_file(filename)
        vm_start(uuid)
    else:
        logging.error('unknown action "%s"' % args.action)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])

