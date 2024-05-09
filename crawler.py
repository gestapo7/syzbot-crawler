import json
import pickle

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
    
    def serialize():
        pass
    
    def deserialize():
        pass

class crawler():
    def __init__():
        pass
