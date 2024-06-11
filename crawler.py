import os
import json
import pickle

OPEN = "https://syzkaller.appspot.com/upstream"
MODERATION = "https://syzkaller.appspot.com/upstream"
FIXED = "https://syzkaller.appspot.com/upstream/fixed"
INVALID = "https://syzkaller.appspot.com/upstream/invalid"

class Data(object):
    """
    hash is the only unique id for data
    """
    def __init__(self, hash = "", dst=""):

        self.url = ""
        self.title = ""
        # address to store data in pickle or json format
        # if hash is None:
        #     print("[-] init failed, we need a unique hash for Data.")
        #     exit(-1)
        # else:
        if hash != "":
            self.hash = hash

        if dst != "":
            if not os.path.exists(dst):
                print("[-] dst do not exist")
            else:
                self.dst = dst

    # def __str__(self):
    #     return '0'

    # def __repr__(self):
    #     return '1'

class DeployData(Data):
    def __init__(self):
        super(DeployData, self).__init__()
        self.patch = ""
        self.assets = False
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

    def serialize(self):
        return

    def deserialize(self):
        return

    def __repr__(self):
        return "DeployData"

    def __str__(self):
        return "DeployData"

class BugData(Data):
    def __init__(self, hash=""):
        super(BugData, self).__init__(hash)
        self.patch = ""
        self.assets = False
        self.repro = False
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

        self.cases[idx]["repro"] = False
        # assets infomation
        if self.assets:
            self.cases[idx]["assets"] = {}
        # manager name
        self.cases[idx]["manager"] = None

    def serialize(self):
        data = {
            "url": self.url,
            "title": self.title,
            "hash": self.hash,
            "patch": self.patch,
            "repro": self.repro,
            "cases": self.cases
        }

        return json.dumps(data, indent=4)

    def deserialize(self):
        pass

    def __repr__(self):
        return "BugData"

    def __str__(self):
        return "BugData"

class ReproduceData(Data):
    def __init__(self):
        super(ReproduceData, self).__init__()

class AssessData(Data):

    def __init__(self):
        super(AssessData, self).__init__()

        # the bug is highrisk or lowrisk (true or false)
        self.highrisk = False
        # addressed by developer (true or false)
        self.address = False
        # reproduced revokled by finder (true or false)
        self.revokled = False
        # the bug has reproducer (true or false)
        self.reproduced = False
        # reproduce instance number
        self.r_count = 0
        # address time, if not address, time=-1
        self.a_time = 0
        # fixed time, if not fixed, time=-1
        self.f_time = 0
        # downstreams fixed time, if not fixed, time=-1
        self.s_time = 0
        # close time, if not close, time=-1
        self.c_time = 0

    def __repr__(self):
        return "AssessData"

    def __str__(self):
        return "AssessData"

class Crawler():
    def __init__():
        pass
