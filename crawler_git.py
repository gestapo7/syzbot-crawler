import re
import sys
import time
import random
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

        self.title = ""
        self.logmsg = ""

        # extract from logmsg through matching by keyword
        self.Desrciption =  ""
        self.Fixes = []
        self.ReportedBy = []
        self.SignedOffBy = []
        self.AckedBy = []
        self.TestedBy = []
        self.ReviewedBy = []
        self.Cc = []

    def __repr__(self):
        raw = ""
        raw += "~~~ Commit Info ~~~\n"
        raw += "author:    {}\n".format(self.author)
        raw += "committer: {}\n".format(self.committer)
        raw += "commit:    {}\n".format(self.commit)
        raw += "tree:      {}\n".format(self.tree)
        raw += "parent:    {}\n".format(self.parent)
        raw += "download:  {}\n".format(self.download)
        raw += "~~~ Commit Log ~~~\n"
        raw += self.Desrciption
        raw += "Fixes:     {}\n".format(self.Fixes)
        raw += "Reported:  {}\n".format(self.ReportedBy)
        raw += "Cc:        {}\n".format(self.Cc )
        raw += "SignedOff: {}\n".format(self.SignedOffBy)
        raw += "Acked:     {}\n".format(self.AckedBy)
        raw += "Tested:    {}\n".format(self.TestedBy)
        raw += "Reviewed:  {}\n".format(self.ReviewedBy)
        return raw

    def __str__(self):
        raw = ""
        raw += "~~~ Commit Info ~~~\n"
        raw += "author:    {}\n".format(self.author)
        raw += "committer: {}\n".format(self.committer)
        raw += "commit:    {}\n".format(self.commit)
        raw += "tree:      {}\n".format(self.tree)
        raw += "parent:    {}\n".format(self.parent)
        raw += "download:  {}\n".format(self.download)
        raw += "~~~ Commit Log ~~~\n"
        raw += self.Desrciption
        raw += "Fixes:     {}\n".format(self.Fixes)
        raw += "Reported:  {}\n".format(self.ReportedBy)
        raw += "Cc:        {}\n".format(self.Cc)
        raw += "SignedOff: {}\n".format(self.SignedOffBy)
        raw += "Acked:     {}\n".format(self.AckedBy)
        raw += "Tested:    {}\n".format(self.TestedBy)
        raw += "Reviewed:  {}\n".format(self.ReviewedBy)
        return raw

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
        try:
            self.info.title = self.soup.find("div", {"class": "commit-subject"}).string
            self.info.logmsg = self.soup.find("div", {"class": "commit-msg"}).string
        except:
            print("[-] wtf, debug ASAP")

        if self.info.logmsg:
            self.__parse_logmsg()

        return

    def __parse_logmsg(self):
        # print(self.info.logmsg)
        lines = self.info.logmsg.split("\n")
        description = []
        for idx, line in enumerate(lines):
            if line.startswith("Fixes: "):
                self.info.Fixes.append(self.strip_prefix(line, "Fixes: "))
            elif line.startswith("Reported-by: "):
                self.info.ReportedBy.append(self.strip_prefix(line, "Reported-by: "))
            elif line.startswith("Signed-off-by: "):
                self.info.SignedOffBy.append(self.strip_prefix(line, "Signed-off-by: "))
            elif line.startswith("Cc: "):
                self.info.Cc.append(self.strip_prefix(line, "Cc: "))
            elif line.startswith("Reviewed-by: "):
                self.info.ReviewedBy.append(self.strip_prefix(line, "Reviewed-by: "))
            elif line.startswith("Acked-by: "):
                self.info.AckedBy.append(self.strip_prefix(line, "Acked-by: "))
            elif line.startswith("Tested-by: "):
                self.info.TestedBy.append(self.strip_prefix(line, "Tested-by: "))
            else:
                description.append(line)

        self.info.Desrciption = "\n".join(description)

if __name__ == "__main__":
    gCrawler = gitCrawler(url = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d624d276d1ddacbcb12ad96832ce0c7b82cd25db")
    gCrawler.parse()
    print(gCrawler.info)