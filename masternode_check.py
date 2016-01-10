#!/usr/bin/python

""" simple 'masternode list' health check """

my_dash_cli = "/home/ubuntu/.dash/dash-cli"
my_mn_conf = "/home/ubuntu/.dash/masternode.conf"


from subprocess import check_output


def run_command(cmd):
    return check_output(cmd, shell=True)


def skip_comments_and_blank(file):
    for line in file:
        line = line.rstrip("\n")
        if line.startswith("#") or not line:
            continue
        yield line


def get_masternodes_from_conf():
    nodes = {}
    with open(my_mn_conf, "r") as f:
        for line in skip_comments_and_blank(f):
            (alias, ip, privkey, vin, n) = line.rstrip("\n").split()
            nodes[vin + '-' + n] = {
                'alias': alias,
                'ip': ip,
                'privkey': privkey,
                'vin': vin,
                'n': n
            }
        return nodes


def get_masternodes_from_dashd():
    nodes = {}
    cmd = " ".join([my_dash_cli, 'masternode list full'])
    node_list = run_command(cmd)
    for line in node_list.split("\n"):
        line = line.translate(None, ''.join('"{}'))
        if not line:
            continue
        (ftx, nop, status, protocol, address, ip,
         last_seen, active, last_paid) = line.split()
        (vin, n) = ftx.split('-')
        nodes[ftx] = {
            'vin': vin,
            'n': n,
            'status': status,
            'protocol': protocol,
            'address': address,
            'ip': ip,
            'last_seen': last_seen,
            'active': active,
            'last_paid': last_paid
        }
    return nodes


def main():
    my_masternodes = get_masternodes_from_conf()
    masternode_list = get_masternodes_from_dashd()

    for my_node in sorted(my_masternodes,
                          key=lambda k: my_masternodes[k]['alias']):
        if my_node in masternode_list:
            if masternode_list[my_node]['status'] == 'ENABLED':
                print (my_masternodes[my_node]['alias'] +
                       " ONLINE - in masternode list")
            else:
                print (my_masternodes[my_node]['alias'] +
                        " OFFLINE -- NOT ENABLED")
        else:
            print (my_masternodes[my_node]['alias'] +
                    " OFFLINE -- NOT IN MASTERNODE LIST")

if __name__ == "__main__":
    main()
