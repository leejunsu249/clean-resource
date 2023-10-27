import os
import sys
import gitlab
from common.k8sclean import k8s as k8sClean
from common.helmclean import deleteHelm
from common.cfClean import cf as cfClean

def make_safe_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def getBranchName(branchName):
    branchName = branchName.split('/')[1:]

    if len(branchName) > 0:
        branchName = "".join("".join(branchName).split('-')[:2]).lower()

    return branchName

def getAppName(projectName):
    return projectName.split('/')[1:][0]

def makeNSName(appName, branchName):
    return appName + "-" + branchName

def clean(token, argotoken, excluded_mr):
    git_url = "gitlab.mgmt.an2.shd.naemo.io"
    git_token  = token


    gl = gitlab.Gitlab("http://" + git_url, private_token=git_token, per_page=50)
    

    naemoGroup = gl.groups.get(13)
    naemoProjects = naemoGroup.projects.list()

    target_dir = os.path.join("./", "temp")
    make_safe_dir(target_dir)

    nsliveBranches = set()

    for project in naemoProjects:
        if "helm" not in project.path_with_namespace and "be-metaverse" not in project.path_with_namespace and "be-systemadmin" not in project.path_with_namespace and "fe-systemadmin" not in project.path_with_namespace:
            liveBranches = set()
            cfliveBranches = set()

            appName = getAppName(project.path_with_namespace)
            projectObj=gl.projects.get(project.id)
            #branches=projectObj.branches.list(get_all=True)

            print("---------" + appName + "---------")

            mrs = projectObj.mergerequests.list(state='opened')

            for mr in mrs:
                nsliveBranches.add(appName + "-" + "mr" + str(mr.iid))
                liveBranches.add("mr" + str(mr.iid))
                cfliveBranches.add("mr" + str(mr.iid))
            
            helm_url = "http://" + "gitlab" + ":" + git_token + "@" + git_url + "/" + project.path_with_namespace + "-helm.git"

            try:
                deleteHelm(helm_url, appName + "-helm", "master", liveBranches, excluded_mr)

            except BaseException as err:
                print("exeption : {0}".format(err))
                pass

            if "fe-" in project.path_with_namespace:
                region = "us-east-2"
                    
                cf = cfClean(region)
                cf.getDeleteStackList(cfliveBranches, appName)               
                cf.deleteStack()

            #cf.deleteAllStackList(excluded_mr)

    k8s = k8sClean("arn:aws:eks:us-east-2:385866877617:cluster/eks-ue2-dev-naemo")
    k8s.getDeleteNSList(nsliveBranches,excluded_mr)
    k8s.deleteNS(argotoken)

if __name__ == '__main__':
    # g_token = os.environ.get("token")
    # argo_token = os.environ.get("argotoken")
    excluded_mr = [""]
    clean(sys.argv[1], sys.argv[2], excluded_mr)

