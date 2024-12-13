# MANDATORY FOR NOW:
# this allows the Manager creation to
# separate from the class that instanced it.
from src.ebs.EBSManager import EBSManager
ebsMgr = EBSManager()
ebsMgr.configure('ebs.json')
