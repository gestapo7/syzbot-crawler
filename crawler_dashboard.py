import json
import datetime
import requests

from bs4 import BeautifulSoup
class uCrawler:
    def __init__(self,
                 url,
                 dst=""
                ):

        self.url = url
        self.cases = {}
        # origin website
        self.soup = None

        self.dst = dst

        curr = datetime.datetime.now()
        # self.csv = "{0}-{1}.csv".format("open", curr.strftime("%Y-%m-%d"))

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
        if len(tables) > 1:
            for _, table in enumerate(tables):
                if table.caption is not None:
                    if table.caption.find("a", {"class", "plain"}) is not None:
                        if table.caption.find("a", {"class", "plain"}).contents[0].find("open") >= 0:
                            self.parse_crash_table(table)
                        # if table.caption.find("a", {"class", "plain"}).contents[0].find("moderation") >= 0:
                            # self.parse_crash_table(table, "moderation")
        elif len(tables) == 1:
            self.parse_crash_table(tables[0], self.url[str.rfind(self.url, "/") + 1:])
        else:
            print("table is none. please check your url!")
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

    def parse_crash_table(self, table):
        cases = self.parse_table_index(table)
        with open(os.path.join(self.dst, self.csv), 'w') as fd:
            newfd = csv.writer(fd)
            for idx, case in enumerate(cases):
                if len(case.find("td", {"class": "stat"}).contents) == 0:
                    url = syzbot_host_url + case.find("td", {"class": "title"}).find('a', href=True).get('href')
                    title = case.find("td", {"class": "title"}).find("a").contents[0]
                    print(url, title)
                    # for every in  case.find_all("td", {"class": "stat"}):
                    #     print(every)
                    newfd.writerow([idx, title, url])
            fd.close()
