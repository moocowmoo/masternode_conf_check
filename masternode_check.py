#!/usr/bin/python

"""
simple masternode status health check using masternode.conf
"""

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
        line = line.translate(None, ''.join(',"{}'))
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
    queue_order = map(
        lambda i: (i, nodes[i]), sorted(
            nodes, key=lambda s: int(nodes[s]['last_paid'])))
    queue_position = 0
    for (ftx, entry) in queue_order:
        queue_position += 1
        nodes[ftx]['queue_position'] = queue_position
        nodes[ftx]['in_selection_queue'] = queue_position <= len(nodes) / 10
    return nodes


def main():
    my_masternodes = get_masternodes_from_conf()
    masternode_list = get_masternodes_from_dashd()

    sort_mode = 'rank'

    def sortby(mode):
        if mode == 'alias':
            return lambda k: my_masternodes[k]['alias'] # noqa
        elif mode == 'rank':
            return lambda k: int(masternode_list[k]['queue_position']) # noqa

    for my_node in sorted(my_masternodes, key=sortby(sort_mode)):
        if my_node in masternode_list:
            if masternode_list[my_node]['status'] == 'ENABLED':
                print "%s %s %4d/%s %s" % (
                    my_masternodes[my_node]['alias'],
                    " ONLINE - in masternode list - rank:",
                    masternode_list[my_node]['queue_position'],
                    len(masternode_list),
                    masternode_list[my_node]['in_selection_queue'] and '(in selection queue)' or ''
                )
            else:
                print (my_masternodes[my_node]['alias'] +
                       " OFFLINE -- NOT ENABLED")
        else:
            print (my_masternodes[my_node]['alias'] +
                   " OFFLINE -- NOT IN MASTERNODE LIST")

if __name__ == "__main__":
    main()
