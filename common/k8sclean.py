import requests
import time
import re
from kubernetes import client, config

class k8s:
    api_client = None
    delNSSet   = set()

    def __init__(self, contextname):
        config.load_kube_config(context=contextname)
        k8s.api_client =  client.CoreV1Api()
    
    def getDeleteNSList(self, liveBranches, excluded_ns):
        nsSet = set()

        pattern = r'mr(\d+)'
        ret = k8s.api_client.list_namespace(watch=False)
        
        for ns in ret.items:
            matches = re.search(pattern, ns.metadata.name)
            if matches and ns.metadata.name.split('-')[-1] not in excluded_ns and ns.metadata.name not in liveBranches:
                nsSet.add(ns.metadata.name)
            else:
                continue   

        k8s.delNSSet = k8s.delNSSet.union(nsSet)

    def deleteNS(self, argotoken):
        for ns in k8s.delNSSet:
            print("Delete NS : " + ns)
            headers = {'Authorization': 'Bearer ' + argotoken }
            url = "http://argo.mgmt.dev.naemo.io/api/v1/applications/" + ns

            res = requests.delete(url, headers=headers)

            print ("sleep 5 seconds from now on...")

            time.sleep(5)
            k8s.api_client.delete_namespace(ns)

        k8s.delNSSet = set()
