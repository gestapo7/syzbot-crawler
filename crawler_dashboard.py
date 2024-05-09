import json
import datetime
import requests
import collections

from bs4 import BeautifulSoup

from crawler import Datastorer

OPEN = "https://syzkaller.appspot.com/upstream"
MODERATION = "https://syzkaller.appspot.com/upstream"
FIXED = "https://syzkaller.appspot.com/upstream/fixed"
INVALID = "https://syzkaller.appspot.com/upstream/invalid"

class dashCrawler:
    def __init__(self,
                 url,
                 dst=""
                ):

        self.url = url
    
        if url in (OPEN, MODERATION, FIXED, INVALID):
            pass
        else:
            print("url is invalid, please check")
            exit(-1)

        self.cases = {}
        # origin website
        self.soup = None

        self.dst = dst

        curr = datetime.datetime.now()
        # self.csv = "{0}-{1}.csv".format("open", curr.strftime("%Y-%m-%d"))
    
    def normalize_url(self, url):
        return "https://syzkaller.appspot.com/" + url

    def parse(self):
        if self.url is None:
            print('invalid url')
            exit(-1)

        req = requests.request(method='GET', url=self.url)
        self.soup = BeautifulSoup(req.text, "html.parser")
        if not self.soup:
            print('soup is none.')
            exit(-1)

        tables = self.parse_table()
        import ipdb; ipdb.set_trace();
        if len(tables) >= 1:
            for _, table in enumerate(tables):
                if table.caption is not None:
                    if table.caption.find("a", {"class", "plain"}) is not None:
                        # open table
                        if "open" in table.caption.find("a", {"class":"plain"}).string.strip():
                            self.parse_open_table(table)
                        # moderation table
                        if "moderation" in table.caption.find("a", {"class", "plain"}).string.strip():
                            self.parse_moderation_table(table)

        elif len(tables) == 1:
            self.parse_crash_table(tables[0], self.url[str.rfind(self.url, "/") + 1:])
        else:
            print("table is none. please check your dashboard url!")
            exit(-1)

    def parse_table(self):
        tables = self.soup.find_all('table', {'class': 'list_table'})
        if len(tables) == 0:
            print("Fail to retrieve bug cases from list_table")
            return []
        else:
            print("[+] table contains {} cases".format(len(tables)))
        return tables

    def parse_table_index(self, table):
        all_cases = table.tbody.find_all('tr')
        return all_cases

    def parse_open_table(self, table):
        cases = self.parse_table_index(table)
        # with open(os.path.join(self.dst, self.csv), 'w') as fd:
            # newfd = csv.writer(fd)
        for idx, case in enumerate(cases):
            if len(case.find("td", {"class": "stat"}).contents) == 0:
                tds = case.find_all("td")
                # for idx,td in enumerate(tds):
                    # pass
                    # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))
                title = tds[0].find("a").string
                url = self.normalize_url(tds[0].find('a').attrs['href'])

                repro = tds[1].string

                cause_bisect = tds[2].string
                fixed_bisect = tds[3].string

                count = tds[4].string
                last = tds[5].string
                reported = tds[6].string

                # TODO: discussion parser
                discussion = tds[7].attrs

                print(idx, repro, cause_bisect, fixed_bisect, count, last, reported, discussion)

                    # print(url, title)
                    # for every in  case.find_all("td", {"class": "stat"}):
                    #     print(every)
                    # newfd.writerow([idx, title, url])
        # fd.close()

    def parse_moderation_table(self, table):
        cases = self.parse_table_index(table)
        # with open(os.path.join(self.dst, self.csv), 'w') as fd:
            # newfd = csv.writer(fd)
        for idx, case in enumerate(cases):
            if len(case.find("td", {"class": "stat"}).contents) == 0:
                tds = case.find_all("td")
                # for idx,td in enumerate(tds):
                    # pass
                    # url = normalize_url(case.find("td", {"class": "title"}).find('a', href=True).get('href'))
                title = tds[0].find("a").string
                url = self.normalize_url(tds[0].find('a').attrs['href'])

                repro = tds[1].string

                cause_bisect = tds[2].string
                fixed_bisect = tds[3].string

                count = tds[4].string
                last = tds[5].string
                reported = tds[6].string

                # TODO: discussion parser
                discussion = tds[7].attrs

                print(idx, repro, cause_bisect, fixed_bisect, count, last, reported, discussion)

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
