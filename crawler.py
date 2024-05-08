import requests
import logging
import sys
import time
import random
import multiprocessing
import json

from bs4 import BeautifulSoup
from prettytable import PrettyTable

syzbot_host_url = "https://syzkaller.appspot.com/"
syzbot_bug_id_url = "bug?id="
syzbot_bug_extid_url = "bug?extid="
supports = {
    0: syzbot_bug_id_url,
    1: syzbot_bug_extid_url
}

class Datastorer():
    def __init__(self, hash, assets=False):

        self.url = ""
        self.title = ""
        self.patch = ""

        if hash is None:
            print("dataStorer init failed")
            exit(-1)
        else:
            self.hash = hash
        self.assets = assets

        self.cases = {}

    def prepare(self, idx):
        self.cases[idx] = {}
        # FIX: catalog: running done failed
        self.cases[idx]['catalog'] = ""

        self.cases[idx]['time'] = None
        # kernel
        self.cases[idx]["kernel"] = None
        self.cases[idx]["commit"] = None
        self.cases[idx]["is_upstream"] = False
        self.cases[idx]["config"] = None
        # syzkaller
        self.cases[idx]["syzkaller"] = None
        # compiler
        self.cases[idx]["gcc"] = None
        self.cases[idx]['clang'] = None
        self.cases[idx]['version'] = None
        # console log
        self.cases[idx]["log"] = None
        # crash
        self.cases[idx]["report"] = None
        # reproduce
        self.cases[idx]["syz"] = None
        self.cases[idx]["cpp"] = None
        # assets infomation
        if self.assets:
            self.cases[idx]["assets"] = {}
        # manager name
        self.cases[idx]["manager"] = None

class Crawler():
    def __init__(self,
                  data,
                  url,
                  type,
                  max=0,
                  debug = False):
        """_summary_

        Args:
            data (Datastorer):
            url (string):
            type (int 0/1):
            debug (bool, default for False):
            assets (bool, default for False):
        """

        if not isinstance(data, Datastorer):
            print("data format can't support!")
            exit(-1)

        self.data = data
        # url type 0,1 or othres
        self.type = type

        self.data.url = url

        self.max = max

        # origin website
        self.soup = None
        self.__init_logger(debug)

    def __init_logger(self, debug):
        handler = logging.StreamHandler(sys.stderr)
        format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(format)
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = True
        else:
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False
        self.logger.addHandler(handler)

    def parse(self):
        try:
            bug_url = supports[self.type]
            self.logger.debug("{}{}{}".format(syzbot_host_url, bug_url, hash))
            url = syzbot_host_url + bug_url + self.data.hash
            if url != self.data.url:
                print("cheking url failed!\n")
                exit(-1)
        except IndexError:
            print("url do not support")
            return

        if self.data.hash is not None:
            """ FIXME: sometime requests can't success, try 5 times
            [proxychains] Strict chain  ...  127.0.0.1:8888  ...  syzkaller.appspot.com:443  ...  OK
            Traceback (most recent call last):
            File "/home/xxx/foobar/syzdirect/syzbuild/main.py", line 225, in <module>
                crawler.parse()
            File "/home/xxx/foobar/syzdirect/syzbuild/modules/crawler.py", line 94, in parse
                self.data.title = self.__parse_title()
                                ^^^^^^^^^^^^^^^^^^^^
            File "/home/xxx/foobar/syzdirect/syzbuild/modules/crawler.py", line 113, in __parse_title
                title = self.soup.body.b.contents[0]
                        ^^^^^^^^^^^^^^^^
            AttributeError: 'NoneType' object has no attribute 'b'
            """
            # retries = 0
            # max_retries = 5
            while True:
                try:
                    req = requests.get(url=url, timeout=5)
                    req.raise_for_status()
                    self.soup = BeautifulSoup(req.text, "html.parser")

                    if not self.soup.body:
                        print("request boby is none, try again")
                    else:
                        print("request boby contains {0} bytes".format(len(req.text)))
                        break
                except requests.RequestException as e:
                    delay = random.uniform(0, 5)
                    print("Request failed: {0}. \nRetrying in {1} seconds...".format(e, delay))
                    time.sleep(delay)
                    # retries = retries+1

        self.data.title = self.__parse_title()
        self.data.patch = self.__parse_patch()

        # TODO: add 
        tables = self.__parse_tables()
        if len(tables) >= 1:
            for i,table in enumerate(tables):
                # NOTE: only consider crashes table
                if table.caption is not None:
                    if table.caption.contents[0].find("Crashes") is not None:
                        # FIX: maybe not the crash table.
                        # sometimes is bisection and so on.
                        ignore = self.__parse_crash_table(table)
                        if not ignore:
                            print("[-] table {} parse failed.".format(i))
                            continue
        else:
            print("[-] table is none.")
            exit(-1)

    def __parse_title(self):
        title = self.soup.body.b.contents[0]
        print("[+] title: ", title)
        return title

    def __parse_tables(self):
        tables = self.soup.find_all('table', {"class": "list_table"})
        if len(tables) == 0:
            print("Fail to retrieve bug cases from list_table")
            return []
        return tables

    def __parse_patch(self):
        patch = None
        mono = self.soup.find("span", {"class": "mono"})
        if mono is None:
            return patch
        try:
            patch = mono.contents[1].attrs['href']
        except:
            pass
        if patch is not None:
            print("[+] patch: ", patch)
        return patch

    def __parse_crash_table(self, table):
        try:
            cases = self.__parse_table_index(table)
            for idx, case in enumerate(cases):
                self.data.prepare(idx)
                self.__parse_kernel_from_case(idx, case)
                self.__parse_commit_from_case(idx, case)
                self.__parse_config_from_case(idx, case)
                self.__parse_log_from_case(idx, case)
                self.__parse_manager_from_case(idx, case)
                self.__parse_time_from_case(idx, case)
                if self.data.assets:
                    self.__parse_assets_from_case(idx, case)
        except:
            self.logger.error("parse crash table failed")
            return False

        # we assume every vulnerability record will contain at least entry which can satisfy our demands
        # let user choice which is better ?
    def __parse_table_index(self, table):
        # FIXME: consider this is no upstream kernel crash
        # like https://syzkaller.appspot.com/bug?extid=c53d4d3ddb327e80bc51
        all_cases = table.tbody.find_all('tr')
        return all_cases

    def __parse_kernel_from_case(self, idx, case):
        cols = case.find_all("td", {"class": "kernel"})
        kernel = cols[0].contents[0]
        if kernel is None:
            print("[-] Warning: kernel is none in url: {}".format(self.data.url))
        else:
            self.data.cases[idx]['kernel'] = kernel
            print("[+] kernel: ", kernel)

        if self.data.cases[idx]['kernel'] == "upstream":
            self.data.cases[idx]["is_upstream"] = True

    def __parse_commit_from_case(self, idx, case):
        cols = case.find_all("td", {"class": "tag"})
        if self.data.cases[idx]['is_upstream']:
            commits = cols[0].contents[0].contents[0]
        else:
            commits = cols[0].contents[0].attrs['href']
        syzkaller = cols[1].contents[0].contents[0]
        if commits is None or syzkaller is None:
            print("[-] Warning: commits or syzkaller is none in url: {}".format(self.data.url))
        else:
            self.data.cases[idx]["commit"] = commits
            print("[+] commit: ", commits)
            self.data.cases[idx]["syzkaller"] = syzkaller
            print("[+] syzkaller: ", syzkaller)

    def __parse_config_from_case(self, idx, case):
        ok = self.data.url.index("bug")
        if ok == -1:
            print("[-] Warning: bug not found in {}".format(self.data.url))
        else:
            prefix = self.data.url[:ok]
            config = case.find("td", {"class": "config"})
            config = prefix + config.contents[0].attrs['href']
            self.data.cases[idx]['config'] = config
            print("[+] config: ", config)
            self.__parse_compiler_version_from_config(idx, config)
            # if self.dst is not None:
            #     req = requests.request(method='GET', url=new_url)
            #     with os.open(os.path.join(self.dst, 'config'), os.O_RDWR | os.O_CREAT) as fd:
            #         os.write(fd, req.text.encode())
            #         os.close(fd)

    def __parse_log_from_case(self, idx, case):
        ok = self.data.url.index("bug")
        if ok == -1:
            print("[-] Warning: bug not found in {}".format(self.data.url))
        else:
            prefix = self.data.url[:ok]
            all = case.find_all("td", {"class": "repro"})
            log,report,syz,cpp,_ = case.find_all("td", {"class": "repro"})

            if log.contents:
                log = prefix + log.contents[0].attrs['href']
                self.data.cases[idx]['log'] = log
                print("[+] console_log: ", log)

            if report.contents:
                report = prefix + report.contents[0].attrs['href']
                self.data.cases[idx]['report'] = report
                print("[+] report: ", report)

            if syz.contents:
                syz = prefix +  syz.contents[0].attrs['href']
                self.data.cases[idx]['syz'] = syz
                print("[+] syz_repro: ", syz)

            if cpp.contents:
                cpp = prefix + cpp.contents[0].attrs['href']
                self.data.cases[idx]['cpp'] = cpp
                print("[+] cpp_repro: ", cpp)

    def __parse_assets_from_case(self, idx, case):
        assets = case.find("td", {"class": "assets"})
        if assets is None:
            return
        spans = assets.find_all("span", {"class": "no-break"})
        print("[+] assets: ")
        for span in spans:
            key = span.contents[1].contents[0]
            value = span.contents[1].attrs['href']
            self.data.cases[idx]['assets'][key] = value

    def __parse_manager_from_case(self, idx, case):
        cols = case.find_all("td", {"class": "manager"})
        manager = cols[0].contents[0]
        if manager is None:
            print("[-] Warning: manager is none in url: {}".format(self.data.url))
        else:
            self.data.cases[idx]['manager'] = manager
            print("[+] manager: ", manager)


    def __parse_time_from_case(self, idx, case):
        time = case.find('td', {"class": "time"}).text

        if time is None:
            print("[-] Warning: time is none in url: {}".format(self.data.url))
        else:
            self.data.cases[idx]['time'] = time

    def __parse_compiler_version_from_config(self, idx, config):
        req = requests.request(method='GET', url=config).text.encode()
        start = req.find(b"CONFIG_CC_VERSION_TEXT=") + len("CONFIG_CC_VERSION_TEXT=")
        if start != -1:
            end = req.find(b"\n", start)
        if end != -1:
            compiler = req[start+1:end-1].decode('utf-8')
            # gcc (GCC) 10.1.0-syz 20200507
            if "gcc" in compiler:
                try:
                    version = compiler.strip().split(' ')[-1]
                    self.data.cases[idx]['version'] = int(version.split('.')[0])
                # FIX: fix weird compiler version string
                except ValueError:
                    self.data.cases[idx]['version']
                    version = ""
                self.data.cases[idx]['gcc'] = "gcc" + version
            # clang 13.0.1-++20220126092033+75e33f71c2da-1~exp1~20220126212112.63
            elif "clang" in compiler:
                try:
                    version = compiler.strip().split(' ')[-1]
                    self.data.cases[idx]['version'] = int(version.split('.')[0])
                # FIX: fix weird compiler version string
                except ValueError:
                    self.data.cases[idx]['version']
                    version = ""
                self.data.cases[idx]['clang'] = "clang"+ version
            else:
                # FIXME: when it's not clang or gcc, will crash in show() function
                # print("do not support this compiler")
                pass
        else:
            print("[-] Warning: can not found gcc version in config")

    def __get_assets(self, case):
        try:
            if case['assets']:
                return "True"
            else:
                return "False"
        except KeyError:
            return "False"

    def show(self):
        table = PrettyTable()
        table.field_names = ["idx", "kernel", "syzkaller", "compiler", "syz", "cpp", "manager", "time", "assets"]
        for idx, case in self.data.cases.items():
            assets = self.__get_assets(case)
            table.add_row([str(idx),
                          str(case["kernel"]),
                          str(case["syzkaller"]),
                          str(case["gcc"]) if case["gcc"] else str(case["clang"]),
                          "True" if case["syz"] else "None",
                          "True" if case["cpp"] else "None",
                          str(case["manager"]),
                          str(case["time"]),
                          assets,
                          ])
        table.title = self.data.hash+ " " + self.data.title
        print(table)

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
        print("url format not support")
        url_flag = 2
        exit(-1)
    return (hash, url_flag)


    # if args.url != None:
    #     hash, url_flag = check_url(args.url)
    #     print("[*] url: {}".format(args.url))
    #     args.dst = os.path.join(args.dst, hash[:8])
    #     if check_dst(args.dst):
    #         run_one(args)

if __name__ == "__main__":
    # print(sys.argv)
    if len(sys.argv) == 2:
        url = sys.argv[1]
        hash, url_flag = check_url(url)
        data = Datastorer(hash)
        crawler = Crawler(data, url, url_flag)
        crawler.parse()
        crawler.show()
    else:
        print("need url link to syzbot")