import os
import sys
import csv
import json

import crawler_git as cg
import crawler_bug as cb
import crawler_lkml as cl
import crawler_dashboard as cd

from crawler import Data,DeployData,BugData,ReproduceData,AssessData

def check_url(url):
    # https://syzkaller.appspot.com/bug?id=1bef50bdd9622a1969608d1090b2b4a588d0c6ac
    hash = ""
    if url.__contains__("bug?id="):
        idx = url.index("bug?id=") + len("bug?id=")
        hash = url[idx:]
        url_flag = 0
    # https://syzkaller.appspot.com/bug?extid=dcc068159182a4c31ca3
    elif url.__contains__("?extid="):
        # test for https://syzkaller.appspot.com/bug?extid=60db9f652c92d5bacba4
        idx = url.index("?extid=") + len("?extid=")
        hash = url[idx:]
        url_flag = 1
    else:
        print("[-] url format not support")
        url_flag = 2
        exit(-1)
    return (hash, url_flag)

    # if args.url != None:
    #     hash, url_flag = check_url(args.url)
    #     print("[*] url: {}".format(args.url))
    #     args.dst = os.path.join(args.dst, hash[:8])
    #     if check_dst(args.dst):
    #         run_one(args)

def args_parse():
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Deploy crash cases from syzbot\n')
    parser.add_argument('-d', '--dst', nargs='?', action='store', help='destination to store.\n'')')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    # args_parse()
    # print(sys.argv)

    url = ""
    if len(sys.argv) == 3:
        which = int(sys.argv[1])
        if which == 1:
            url = "https://syzkaller.appspot.com/upstream"
        elif which ==2:
            url = "https://syzkaller.appspot.com/upstream/fixed"
        elif which ==3:
            url = "https://syzkaller.appspot.com/upstream/invalid"
        else:
            print("erro url link to syzbot")
            exit(-1)

        where = sys.argv[2]
        if not os.path.exists(where):
            print("error dst not existed")
            exit(-1)
    else:
        print("erro args")
        exit(-1)

    bd = BugData()

    dCrawler = cd.dashCrawler(url, data=bd, nested=True, dst=where)
    dCrawler.parse()

    # dst = "/home/tomcat/ESCAPE/yome-syzbots"
    # dCrawler.save(where, onlyLog=True)