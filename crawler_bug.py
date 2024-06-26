import re
import os
import bs4
import sys
import json
import glob
import time
import shutil
import random
import logging
import requests
import traceback
import multiprocessing

from IPython import embed
from bs4 import BeautifulSoup
from prettytable import PrettyTable

from crawler import Crawler
from crawler import BugData

syzbot_host_url = "https://syzkaller.appspot.com/"
syzbot_bug_id_url = "bug?id="
syzbot_bug_extid_url = "bug?extid="
supports = {
    0: syzbot_bug_id_url,
    1: syzbot_bug_extid_url
}

# REPRO TAG
REPRO_SUCCESS = "1"
REPRO_FAILED = "0"

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

class MeanlessUrl(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class bugCrawler(Crawler):
    def __init__(self,
                 url,
                 title,
                 flag,
                 data,
                 max = 0,
                 debug = False):
        """_summary_
        Args:
            data (DeployData):
            url (string):
            type (int 0/1):
            debug (bool, default for False):
            assets (bool, default for False):
        """

        if not isinstance(data, BugData):
            print("data format can't support!")
            exit(-1)

        self.data = data

        # url type 0,1 or othres
        self.flag = flag

        self.data.url = url
        self.data.title = title

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
            bug_url = supports[self.flag]
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
            if not self.data.url:
                print("url is none, wtf ???")
                import ipdb; ipdb.set_trace()

            while True:
                try:
                    req = requests.Session().get(url=self.data.url, timeout=5)
                    req.raise_for_status()
                    self.soup = BeautifulSoup(req.text, "html.parser")

                    if not self.soup.body:
                        print("request boby is none, try again")
                    else:
                        print("request boby contains {0} bytes".format(len(req.text)))
                        break
                except requests.RequestException as e:
                    delay = random.uniform(0, 3)
                    print("Request failed: {0}. \nRetrying in {1} seconds...".format(e, delay))
                    time.sleep(delay)
                except:
                    import ipdb; ipdb.set_trace();

        self.data.title = self.__parse_title()
        self.data.patch = self.__parse_patch()

        self.__parse_bisection()
        self.__parse_discussion()
        self.__parse_lastpatchrequests()

        tables = self.__parse_tables()
        if len(tables) >= 1:
            for i,table in enumerate(tables):
                # NOTE: only consider crashes table
                if table.caption is not None:
                    if "Crashes" in table.caption.contents[0]:
                        # FIX: maybe not the crash table.
                        # sometimes is bisection and so on.
                        ignore = self.__parse_crash_table(table)
                        if not ignore:
                            print("[-] table {} parse failed.".format(i))
                            continue
        else:
            print("[-] table is none.")
            exit(-1)

    def filter(self):
        pass


    def save(self, dst, repro=False, save_bug=False, save_log=False):
        if not os.path.exists(dst):
            print("bug saves {0} don't exists".format(dst))
            os.makedirs(dst)

        folder = os.path.join(dst, self.data.hash)

        if repro:
            if self.data.repro:
                folder = folder + "-" + REPRO_SUCCESS
            else:
                folder = folder + "-" + REPRO_FAILED

        if not os.path.exists(folder):
            print("create folder {0}".format(folder))
            os.makedirs(folder)
        else:
            print("bug folder is created.")

        if save_bug:
            data = self.data.serialize()
            # import ipdb; ipdb.set_trace()
            if data:
                file = os.path.join(folder, self.data.hash + ".json")
                # FIXME: now force replace all because previous are wrong
                # if not os.path.exists(file):
                with open(file, 'w') as f:
                    # NOTE: json is ok... what are you doing...
                    f.write(data)
                # else:
                #     print("json file is created")
            else:
                print("data serialize failed or data failed")

        if save_log:
            logs = glob.glob(os.path.join(folder, "log*"))
            if len(logs) == len(self.data.cases):
                print("logs are downloaded")
            else:
                ignore = self.__save_logs(folder, repro=repro)
                if ignore:
                    print("save logs done")
                else:
                    print("save logs failed")
        return

    def __save_logs(self, dst, repro=False):
        # TODO: add multiprocess for this deploy prograss
        for idx, case in self.data.cases.items():
            if not os.path.exists(os.path.join(dst, 'log{}'.format(idx))):
                # FIXME: add reconnect for request in this part
                if not case['log']:
                    # import ipdb; ipdb.set_trace();
                    print("[-] url is none")
                    continue

                while True:
                    try:
                        req = requests.Session().get(url=case['log'], timeout=5)
                        req.raise_for_status()

                        if repro:
                            log = os.path.join(dst, 'log{}'.format(idx))
                        else:
                            log = os.path.join(dst, 'log{}'.format(idx))

                        if req.text:
                            print("downloading log{0} for {1} bytes".format(idx, len(req.text)))
                            with open(log, "wb") as fd:
                                fd.write(req.text.encode())
                            break
                    except requests.RequestException as e:
                        delay = random.uniform(0, 3)
                        print("Request failed: {0}. \nRetrying in {1} seconds...".format(e, delay))
                        # import ipdb; ipdb.set_trace();
                        time.sleep(delay)
                        # retries = retries+1
                    except:
                        print("what happened!")
                        import ipdb; ipdb.set_trace();
        return True


    def __parse_title(self):
        title = self.soup.body.b.contents[0]
        print("[+] title: ", title)
        return title

    def __parse_tables(self):
        tables = self.soup.find_all('table', {"class": "list_table"})
        if len(tables) == 0:
            print("[-] Failed to retrieve bug cases from list_table")
            return []
        return tables

    # TODO: add bisection parser
    def __parse_bisection(self):
        """
        return cause_bisection_url, fixed_bisection_url
        """
        bisection = self.soup.find_all('div', {"class":"bug-bisection-info"})

        cause_bisection,fixed_bisection = None,None
        if len(bisection) == 2:
            cause_bisection = bisection[0]
            fixed_bisection = bisection[1]
        elif len(bisection) == 1:
            cause_bisection = bisection[0]
        elif len(bisection) == 0:
            return None, None
        else:
            print("[-] why there are multi bug-bisection-infos")
            exit(-1)

        cause_bisection_url,fixed_bisection_url = None, None
        if cause_bisection:
            cause = cause_bisection.find('b').string
            if cause == "Cause bisection: introduced by":
                try:
                    cause_bisection_url = cause_bisection.find('br').find('a').attrs['href']
                except AttributeError:
                    cause_bisection_url = cause_bisection.find('br').find('a')

        if fixed_bisection:
            fixed = fixed_bisection.find('b').string
            if fixed == "Fix bisection: fixed by":
                try:
                    fixed_bisection_url = fixed_bisection.find('br').find('a').attrs['href']
                except AttributeError:
                    fixed_bisection_url = fixed_bisection.find('br').find('a')

        return cause_bisection_url, fixed_bisection_url

    def __parse_discussion(self):
        """
        return discussion_url(string[]), address(bool)
        """
        # find discussions table first
        discussion_url = []
        address = False

        span_tag = self.soup.find_all('span', string=re.compile(r'Discussions \(\d+\)'))
        if len(span_tag) == 1:
            div_head = span_tag[0].find_parent('div', class_='head')
            div_content = div_head.find_next_sibling('div', class_='content')
            table = div_content.find('table', class_='list_table')
            try:
                cases = self.__parse_table_index(table)
                for case in cases:
                    tds = case.find_all("td")
                    discussion_url.append(tds[0].find('a').attrs['href'])
                    match = re.match(r"(\d+)\s*\((\d+)\)", tds[1].string)
                    if match:
                        bot = match.group(1)
                        all = match.group(2)
                        # print(bot, all)
                        if bot!=0:
                            address=True
            except:
                self.logger.error("parse discussion table failed")
                return None, None
        elif len(span_tag) ==0:
            return None, None
        else:
            import ipdb; ipdb.set_trace();
            print("[-] why there are multi discussion table")
            exit(-1)

        return discussion_url, address

    def __parse_patch(self):
        """
        return patch commit url add by maintainer
        """
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
    
    def __parse_lastpatchrequests(self):
        pass

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

                # TODO: revoke data.assets
                # if self.data.assets:
                    # self.__parse_assets_from_case(idx, case)
            # whatever true!!!
            # mustbe true!!!
            return True
        except MeanlessUrl as e:
            self.logger.error("{0}".format(e))
            return False
        except Exception as e:
            traceback.print_exc()
            self.logger.error("parse crash table failed: {0}".format(e))
            import ipdb; ipdb.set_trace();
            return False
        # we assume every bug will contain at least one entry which satisfy us?
        # let user choice which is better ?
    def __parse_table_index(self, table):
        # like https://syzkaller.appspot.com/bug?extid=c53d4d3ddb327e80bc51
        all_cases = table.tbody.find_all('tr')

        # FIXME: There is Last patch testing requests table
        return all_cases

    def __parse_kernel_from_case(self, idx, case):
        cols = case.find_all("td", {"class": "kernel"})
        # print(cols)
        if cols == []:
            import ipdb; ipdb.set_trace();

        kernel = cols[0].contents[0]
        if kernel is None:
            print("[-] Warning: kernel is none in url: {}".format(self.data.url))
        else:
            # HACK: fuck https://syzkaller.appspot.com/bug?id=2c552e46576265a611ece4cbd486455d3462daa0
            if "syzkaller" in kernel:
                # import ipdb; ipdb.set_trace();
                raise MeanlessUrl("{0} is useless".format(self.data.hash))
            self.data.cases[idx]['kernel'] = kernel
            print("[+] kernel: ", kernel)

        if self.data.cases[idx]['kernel'] == "upstream":
            self.data.cases[idx]["is_upstream"] = True

    def __parse_commit_from_case(self, idx, case):
        cols = case.find_all("td", {"class": "tag"})
        if self.data.cases[idx]['is_upstream']:
            commits = cols[0].contents[0].contents[0]
        else:
            # HACK:
            # https://syzkaller.appspot.com/bug?extid=29cc278357da941e304e
            # mmots ce3c209f6733
            try:
                commits = cols[0].contents[0].attrs['href']
            except AttributeError:
                commits = cols[0].contents[0]
            finally:
                print("[+] commit: ", commits)
                
        syzkaller = cols[1].contents[0].contents[0]
        print("[+] syzkaller: ", syzkaller)
        if commits is None or syzkaller is None:
            print("[-] Warning: commits or syzkaller is none in url: {}".format(self.data.url))
        else:
            self.data.cases[idx]["commit"] = commits
            self.data.cases[idx]["syzkaller"] = syzkaller

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

            # self.__parse_compiler_version_from_config(idx, config)

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
            log,report,syz,cpp,_ = case.find_all("td", {"class": ["repro", "repro stale_repro"]})

            if log.contents:
                try:
                    log = prefix + log.contents[0].attrs['href']
                    print("[+] console_log: ", log)
                except AttributeError:
                    log = None
                self.data.cases[idx]['log'] = log

            if report.contents:
                try:
                    report = prefix + report.contents[0].attrs['href']
                    print("[+] report: ", report)
                except AttributeError:
                    report = None
                self.data.cases[idx]['report'] = report

            syz_revoked = 'stale_repro' in syz.get("class")
            syz_content = [item for item in syz.contents if isinstance(item, bs4.element.Tag)]
            if syz_content:
                try:
                    # FIXME: filter "\n" or sth annoy me !!!
                    # import ipdb; ipdb.set_trace();
                    syz = prefix + syz_content[0].attrs['href']
                    print("[+] syz_repro: ", syz)
                    self.data.repro = True
                except AttributeError:
                    syz = None
                self.data.cases[idx]['syz'] = syz

            cpp_revoked = 'stale_repro' in cpp.get("class") 
            cpp_content = [item for item in cpp.contents if isinstance(item, bs4.element.Tag)]
            if cpp_content:
                try:
                    cpp = prefix + cpp_content[0].attrs['href']
                    print("[+] cpp_repro: ", cpp)
                    self.data.repro = True
                except AttributeError:
                    cpp = None
                self.data.cases[idx]['cpp'] = cpp

            # FIXME: judge syz repro or c repro vaild or not
            self.data.cases[idx]['repro'] = False
            # add self.data.cases[idx] repro
            if (self.data.cases[idx]['cpp'] and not cpp_revoked) or (self.data.cases[idx]['syz'] and not syz_revoked):
                # import ipdb; ipdb.set_trace()
                self.data.cases[idx]['repro'] = True

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
        while True:
            try:
                req = requests.get(url=config, timeout=5)
                req.raise_for_status()
                # self.soup = BeautifulSoup(req.text, "html.parser")

                if not req.text:
                    print("request boby is none, try again")
                else:
                    print("request boby contains {0} bytes".format(len(req.text)))
                    break
            except requests.RequestException as e:
                delay = random.uniform(0, 5)
                print("Request failed: {0}. \nRetrying in {1} seconds...".format(e, delay))
                time.sleep(delay)

        cnt = req.text.encode()
        start = cnt.find(b"CONFIG_CC_VERSION_TEXT=") + len("CONFIG_CC_VERSION_TEXT=")
        if start != -1:
            end = cnt.find(b"\n", start)
        if end != -1:
            compiler = cnt[start+1:end-1].decode('utf-8')
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


if __name__ == "__main__":
    # url = "https://syzkaller.appspot.com/bug?id=d5d780ebdea00d45e7dcca8b25d9d7d2aff7da6c"
    # url = "https://syzkaller.appspot.com/bug?id=30466236e69668c67b90c8988ee44a85794222ae"
    # url = "https://syzkaller.appspot.com/bug?id=131df746862cee15e5b8c4f879524e8eececafd3"
    url = "https://syzkaller.appspot.com/bug?id=c7f32230a7e2f3a034a3355feffca8e41bee900a"
    title = "4"
    hash, flag = check_url(url)

    data = BugData(hash)
    bug = bugCrawler(url=url,
                     title=title,
                     flag=flag,
                     data=data)
    bug.parse()
    bug.show() 
    bug.save("/home/tomcat/ESCAPE/yome-syzbots/invalid", repro=True, save_log=True, save_bug=True)
    