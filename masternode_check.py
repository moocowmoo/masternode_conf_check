#!/usr/bin/python

"""
simple masternode status health check using masternode.conf
"""

my_dash_cli = "/home/ubuntu/.dash/dash-cli"
my_mn_conf = "/home/ubuntu/.dash/masternode.conf"


import time
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
    t_now = int(time.time())

    for line in node_list.split("\n"):
        line = line.translate(None, ''.join(',"{}'))
        if not line:
            continue
        (ftx, nop, status, protocol, address, ip,
         last_seen, active, last_paid) = line.split()
        (vin, n) = ftx.split('-')
        # **estimate how many blocks since paid
        blocks_since_paid = int(float(int(t_now) - int(last_paid)) / 150)
        nodes[ftx] = {
            'vin': vin,
            'n': n,
            'status': status,
            'protocol': protocol,
            'address': address,
            'ip': ip,
            'last_seen': last_seen,
            'active': active,
            'last_paid': last_paid,
            'blocks_since_paid': blocks_since_paid
        }
    queue_order = list(enumerate(map(lambda ftx: ftx, sorted(
                       nodes, key=lambda s: int(nodes[s]['last_paid'])))))
    for (pos, ftx) in queue_order:
        n = nodes[ftx]
        n['queue_position'] = pos
        n['in_selection_queue'] = pos <= len(nodes) / 10
        if n['in_selection_queue']:
            # calculate selection probability
            p_pool = len(nodes) / 10
            b_count = n['blocks_since_paid'] - (len(nodes) - p_pool)
            p_prob = 1.0 - ((float(p_pool-1)/float(p_pool)) ** float(b_count))
            n['selection_probability'] = p_prob
    return nodes


def main(sort_mode='rank'):
    my_masternodes = get_masternodes_from_conf()
    masternode_list = get_masternodes_from_dashd()

    def sortby(mode):
        if mode == 'alias':
            return lambda k: my_masternodes[k]['alias']  # noqa
        elif mode == 'rank':
            return lambda k: (  # noqa
                              k in masternode_list
                              and int(masternode_list[k]['queue_position'])
                              or 0)

    for my_node in sorted(my_masternodes, key=sortby(sort_mode)):
        if my_node in masternode_list:
            n = masternode_list[my_node]
            if n['status'] == 'ENABLED':
                sel_txt = ''
                if n['in_selection_queue']:
                    sel_txt = ("(in selection queue) probability: {:0.2f}%"
                               .format(n['selection_probability'] * 100))
                print "%s %s %4d/%s %s" % (
                    my_masternodes[my_node]['alias'],
                    " ONLINE - in masternode list - rank:",
                    n['queue_position'],
                    len(masternode_list),
                    sel_txt
                )
            else:
                print (my_masternodes[my_node]['alias'] +
                       " OFFLINE -- NOT ENABLED")
        else:
            print (my_masternodes[my_node]['alias'] +
                   " OFFLINE -- NOT IN MASTERNODE LIST")

if __name__ == "__main__":
    main()
