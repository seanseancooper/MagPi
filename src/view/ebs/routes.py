# MANDATORY FOR NOW:
# this allows the Manager creation to
# separate from the class that instanced it.
from src.view.ebs.EBSManager import EBSManager
ebsMgr = EBSManager()
ebsMgr.configure('ebs.json')
