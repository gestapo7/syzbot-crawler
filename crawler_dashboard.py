import os
import json
import datetime
import requests
import collections

from bs4 import BeautifulSoup

from crawler import BugData,DeployData,ReproduceData,AssessData
from crawler import Crawler

import crawler_bug as cb
import crawler_git as cg
import crawler_lkml as cl
import crawler_dashboard as cd

VALID_URLS = ""
OPEN = "https://syzkaller.appspot.com/upstream"
MODERATION = "https://syzkaller.appspot.com/upstream"
FIXED = "https://syzkaller.appspot.com/upstream/fixed"
INVALID = "https://syzkaller.appspot.com/upstream/invalid"

def check_url(url):
    """
    return 2 types of the url
    """
    ID = 0
    EXTID = 1
    ERROR = 2
    # https://syzkaller.appspot.com/bug?id=1bef50bdd9622a1969608d1090b2b4a588d0c6ac
    hash = ""
    if url.__contains__("bug?id="):
        idx = url.index("bug?id=") + len("bug?id=")
        hash = url[idx:]
        type = ID
    # https://syzkaller.appspot.com/bug?extid=dcc068159182a4c31ca3
    elif url.__contains__("?extid="):
        # test for https://syzkaller.appspot.com/bug?extid=60db9f652c92d5bacba4
        idx = url.index("?extid=") + len("?extid=")
        hash = url[idx:]
        type = EXTID
    else:
        print("[-] url format not support")
        type = ERROR
        exit(-1)
    return (hash, type)


class Dashboard():
    def __init__(self):
        pass

    def save(self):
        pass

class dashCrawler(Crawler):
    """
    mode:
        1. nested
        2. all
    """
    def __init__(self,
                 url,
                 mode=0,
                 data=None,
                 nested=False,
                 dst=""):

        self.url = url

        if url in (OPEN, MODERATION, FIXED, INVALID):
            pass
        else:
            print("url is invalid, please check")
            exit(-1)

        self.data = data
        # origin website
        self.soup = None
        self.cases = {}

        self.dst = dst

        curr = datetime.datetime.now()
        print('[+] {}'.format(curr.strftime("%y-%m-%d")))
        print('[+] {}'.format(self.url))

        self.nested_mode = False

        if isinstance(data, AssessData):
            self.nested = True

        if isinstance(data, BugData):
            self.nested = True

        self.open_table = []
        self.fixed_table = []
        self.invalid_table = []
        self.moderation_table = []
        # self.csv = "{0}-{1}.csv".format("open", curr.strftime("%Y-%m-%d"))

    def normalize_url(self, url):
        return "https://syzkaller.appspot.com" + url

    def normalize_str(self, s):
        if s:
            return s.strip()
        else:
            return s

    def parse_open(self):
        # if not isinstance(self.data, AssessData):
        #     return

        # cb.bugCrawler(url=table[1])
        print(self.open_table)
        try:
            for idx,cnt in enumerate(self.open_table):
                print(idx, cnt[0])
                title = cnt[0]
                url = cnt[1]
                hash, type = check_url(url)

                data = BugData(hash)
                bug = cb.bugCrawler(url=url,
                                    title=title,
                                    type=type,
                                    data=data)
                bug.parse()
                bug.show()
                bug.save(dst="/home/spark/ESCAPE/yome-syzbots/open", repro=True, save_log=True)

        except KeyboardInterrupt:
            exit(-1)

    def assess_parse_moderation(self, table):
        pass

    def assess_parse_fixed(self, table):
        pass

    def assess_parse_invalid(self, table):
        pass

    def parse(self):
        if self.url is None:
            print('invalid url')
            exit(-1)

        # FIXME: quick request with session
        req = requests.Session().get(url=self.url)
        # req = requests.request(method='GET', url=self.url)
        self.soup = BeautifulSoup(req.text, "html.parser")
        if not self.soup:
            print('soup is none.')
            exit(-1)

        if self.url == OPEN:
            tables = self.__parse_table()
            if len(tables) >= 1:
                for _, table in enumerate(tables):
                    if table.caption is not None:
                        if table.caption.find("a", {"class", "plain"}) is not None:
                            # open table
                            if "open" in table.caption.find("a", {"class":"plain"}).string.strip():
                                self.__parse_open_table(table)
                            # moderation table
                            if "moderation" in table.caption.find("a", {"class", "plain"}).string.strip():
                                self.__parse_moderation_table(table)

            else:
                print("table is none. please check your dashboard url!")
                exit(-1)

        elif self.url == FIXED:
            tables = self.__parse_table()
            if len(tables) == 1:
                self.__parse_fixed_table(tables[0])

        elif self.url == INVALID:
            tables = self.__parse_table()
            if len(tables) == 1:
                self.__parse_invalid_table(tables[0])

        else:
            print("invalid url")
            exit(-1)


    def save(self, dst, onlyLog=False):
        if not os.path.exists(dst):
            print("dst don't exists")
            exit(-1)
        import ipdb;ipdb.set_trace();


    def __parse_table(self):
        tables = self.soup.find_all('table', {'class': 'list_table'})
        if len(tables) == 0:
            print("[-] failed to retrieve bug cases from soup")
            return None
        else:
            print("[+] soup contains {} tables".format(len(tables)))
        return tables


    def __parse_table_index(self, table):
        cases = table.tbody.find_all('tr')
        if len(cases) == 0:
            print("[-] failed to retrieve bug cases from table")
            return None
        else:
            print('[+] table contains {} cases'.format(len(cases)))
        return cases


    def __parse_open_table(self, table):
        cases = self.__parse_table_index(table)
        # with open(os.path.join(self.dst, self.csv), 'w') as fd:
            # newfd = csv.writer(fd)
        self.open_table = []
        for _, case in enumerate(cases):
            if len(case.find("td", {"class": "stat"}).contents) == 0:
                tds = case.find_all("td")
                # for idx,td in enumerate(tds):
                    # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))
                try:
                    title = tds[0].find("a").string
                    url = self.normalize_url(tds[0].find('a').attrs['href'])
                    repro = tds[1].string
                    cause_bisect = tds[2].string
                    fixed_bisect = tds[3].string
                    count = tds[4].string
                    last = tds[5].string
                    reported = tds[6].string
                    discussions = tds[7].text if tds[7].text is not None else ''
                    self.open_table.append([title, url, repro, cause_bisect, fixed_bisect, count, last, reported, discussions])
                    print(title, url, repro, cause_bisect, fixed_bisect, count, last, reported, discussions)
                except Exception as e:
                    print("wtf man, {0}".format(e))
                    exit(-1)

        if self.nested:
            self.parse_open()
                # print(url, title)
                # for every in  case.find_all("td", {"class": "stat"}):
                #     print(every)
                # newfd.writerow([idx, title, url])

        # fd.close()

    def __parse_moderation_table(self, table):
        cases = self.__parse_table_index(table)
        # with open(os.path.join(self.dst, self.csv), 'w') as fd:
            # newfd = csv.writer(fd)
        for idx, case in enumerate(cases):
            if len(case.find("td", {"class": "stat"}).contents) == 0:
                tds = case.find_all("td")
                # for idx,td in enumerate(tds):
                    # pass
                    # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))
                try:
                    title = tds[0].find("a").string
                    url = self.normalize_url(tds[0].find('a').attrs['href'])
                    repro = self.normalize_str(tds[1].string)
                    cause_bisect = tds[2].string
                    fixed_bisect = tds[3].string
                    count = tds[4].string
                    last = tds[5].string
                    reported = tds[6].string
                    # TODO: discussion parser
                    discussions = tds[7].text if tds[7].text is not None else ''
                except Exception as e:
                    print("wtf man, {0}".format(e))
                    exit(-1)

                # print(idx, repro, cause_bisect, fixed_bisect, count, last, reported, discussions)
                # self.assess_parse_open()

        # cases = self.parse_table_index(table)
        # with open(os.path.join(self.dst, self.csv), 'w') as fd:
            # newfd = csv.writer(fd)
        # for idx, case in enumerate(cases):
            # if len(case.find("td", {"class": "stat"}).contents) == 0:
                # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))
                # title = case.find("td", {"class": "title"}).find("a").contents[0]
                # print(url, title)
                    # for every in  case.find_all("td", {"class": "stat"}):
                    #     print(every)
                    # newfd.writerow([idx, title, url])
        # fd.close()

    def __parse_fixed_table(self, table):
        cases = self.__parse_table_index(table)
        # with open(os.path.join(self.dst, self.csv), 'w') as fd:
            # newfd = csv.writer(fd)
        for idx, case in enumerate(cases):
            tds = case.find_all("td")

            # for idx,td in enumerate(tds):
                # pass
                # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))

            title = tds[0].find("a").string
            url = self.normalize_url(tds[0].find('a').attrs['href'])
            repro = self.normalize_str(tds[1].string)
            # bisection infos
            cause_bisect = self.normalize_str(tds[2].string)
            fixed_bisect = self.normalize_str(tds[3].string)
            count = int(tds[4].string)
            last = self.normalize_str(tds[5].string)
            reported = self.normalize_str(tds[6].string)
            patched = self.normalize_str(tds[7].string)
            closed = self.normalize_str(tds[8].string)
            # TODO: patch parser
            cnt = tds[9].find("span", {"class":"mono"})
            if cnt:
                try:
                    patch_commit = cnt.a['href']
                except TypeError:
                    # TODO: use description to find in git.kernel.org
                    patch_commit = None
                    patch_depict = cnt.string
                else:
                    patch_depict = self.normalize_str(cnt.a.string)

            print(idx, title, url, repro, cause_bisect, fixed_bisect, count, last, reported, patched, closed, patch_commit, patch_depict)


    def __parse_invalid_table(self, table):
        cases = self.__parse_table_index(table)
        for idx, case in enumerate(cases):
            if len(case.find("td", {"class": "stat"}).contents) == 0:
                tds = case.find_all("td")
                # for idx,td in enumerate(tds):
                    # pass
                    # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))
                title = tds[0].find("a").string
                url = self.normalize_url(tds[0].find('a').attrs['href'])
                repro = self.normalize_str(tds[1].string)
                cause_bisect = self.normalize_str(tds[2].string)
                fixed_bisect = self.normalize_str(tds[3].string)
                count = self.normalize_str(tds[4].string)
                last = self.normalize_str(tds[5].string)
                reported = self.normalize_str(tds[6].string)
                print(idx, title, url, repro, cause_bisect, fixed_bisect, count, last, reported)