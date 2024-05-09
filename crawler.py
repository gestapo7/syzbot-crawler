import os
import json
import pickle

class Data:
    """
    hash is the only unique id for data
    """
    def __init__(self, hash, dst=""):

        self.url = ""
        self.title = ""
        # address to store data in pickle or json format
        if hash is None:
            print("[-] init failed, we need a unique hash for Data.")
            exit(-1)
        else:
            self.hash = hash

        if not os.path.exists(dst):
            print("[-] dst do not exist")
        else:
            self.dst = dst
    
    def __str__(self):
        return '0'
    
    def __repr__(self):
        return '1'

class DeployData(Data):
    def __init__(self, hash, assets=False):
        super.__init__(hash)
        self.patch = ""
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
    
    def serialize():
        pass
    
    def deserialize():
        pass

class ReproduceData(Data):
    def __init__(self, hash, assets=False):
        super.__init__(hash)

class AssessData(Data):
    def __init__(self, hash, assets=False):
        super.__init__(hash)


class Crawler():
    def __init__():
        pass
