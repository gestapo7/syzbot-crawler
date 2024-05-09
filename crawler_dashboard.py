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
                 dst=""):

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
        print('[+] {}'.format(curr.strftime("%y-%m-%d")))
        print('[+] {}'.format(self.url))
        # self.csv = "{0}-{1}.csv".format("open", curr.strftime("%Y-%m-%d"))
    
    def normalize_url(self, url):
        return "https://syzkaller.appspot.com/" + url
    
    def normalize_str(self, s):
        if s:
            return s.strip()
        else:
            return s

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

    def __parse_moderation_table(self, table):
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

                repro = self.normalize_str(tds[1].string)

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
        pass

if __name__ == "__main__":
    crawler = dashCrawler("https://syzkaller.appspot.com/upstream/fixed")
    crawler.parse()
