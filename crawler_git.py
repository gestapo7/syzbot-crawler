import requests
import datetime

from crawler import Crawler
from bs4 import BeautifulSoup

# simple git info only for us
class gitInfo():
    def __init__(self):
        self.author = ""
        self.committer = ""
        self.commit = ""
        self.tree = ""
        self.parent = ""
        self.download = ""

        self.logmsg = ""

        # extract from logmsg through matching by keyword
        self.Desrciption = ""
        self.ReportedBy = []
        self.SignedOffBy = []
        self.CC = []
    
    def __str__():
        pass
    
    def __repr__():
        pass

# WebCrawler for git.kernel.org
class gitCrawler(Crawler):
    def __init__(self,
                 url,
                 dst=""):

        self.url = url
    
        if not url.startswith("https://git.kernel.org/"):
            print("[-] url is invalid, please check, mustbe git.kernel.org")
            exit(-1)

        self.cases = {}
        # origin website
        self.soup = None

        self.dst = dst
        self.info = gitInfo()

        curr = datetime.datetime.now()
        print('[+] {}'.format(curr.strftime("%y-%m-%d")))
        print('[+] {}'.format(self.url))

    def __parse_table(self):
        tables = self.soup.find_all('table', {'class': 'list_table'})
        if len(tables) == 0:
            print("[-] failed to retrieve bug cases from soup")
            return None
        else:
            print("[+] soup contains {} tables".format(len(tables)))
        return tables

    def __parse_table_index(self, table):
        if table.tbody:
            cases = table.tbody.find_all('tr')
        else:
            cases = table.find_all('tr')

        if len(cases) == 0:
            print("[-] failed to retrieve bug cases from table")
            return None
        else:
            print('[+] table contains {} cases'.format(len(cases)))
        return cases
    
    def strip_prefix(self, msg, prefix):
        if msg.startswith(prefix):
            return msg[len(prefix)-1:].strip()
        else:
            return msg

    def parse(self):
        retries = 0
        max = 5
        while True:
            try:
                if retries > max:
                    break
                req = requests.Session().get(url=self.url, timeout=5)
                req.raise_for_status()
                self.soup = BeautifulSoup(req.text, "html.parser")

                if not self.soup.body:
                    print("[-] request boby is none, try again")
                else:
                    print("[+] request boby contains {0} bytes".format(len(req.text)))
                    break

            except requests.RequestException as e:
                print("[-] Request failed: {0}. \nRetrying in {1} seconds...".format(e, delay))
                delay = random.uniform(0, 5)
                time.sleep(delay) 
                retries += 1

        content = self.soup.find("div", {"class":"content"})
        if content:
            commit_info = content.find("table",{"class":"commit-info"})
            if commit_info:
                tds = self.__parse_table_index(commit_info)

                self.info.author = self.strip_prefix(tds[0].text, "author")
                self.info.committer = self.strip_prefix(tds[1].text, "committer")
                self.info.commit = self.strip_prefix(tds[2].text, "commit")
                self.info.tree = self.strip_prefix(tds[3].text, "tree")
                self.info.parent = self.strip_prefix(tds[4].text, "parent")
                self.info.download = tds[5].a['href']

        return

if __name__ == "__main__":
    gCrawler = gitCrawler(url = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d624d276d1ddacbcb12ad96832ce0c7b82cd25db")
    gCrawler.parse()
    import ipdb; ipdb.set_trace()
    # print(gCrawler.info)
