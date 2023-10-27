import os
import shutil
import git


def deleteHelm(helm_url, appName, branchName, liveBranches, excluded_mr):

    repo = git.Repo.clone_from(helm_url, "temp/" , branch=branchName)
    
    if os.path.exists("temp/" + "feature"):
        file_list = os.listdir("temp/"  + "feature")
        branch_list = ["values-" + x + ".yaml" for x in liveBranches]

        for file in file_list:
            if file not in branch_list and file != "values-template.yaml" and file.split('-')[-1].split('.')[0] not in excluded_mr:
                print("deletefile :  " + branchName + " " + file)
                os.remove("temp/" + "feature/" + file)
            else: 
                continue

        try:
            repo = git.Repo("temp/" + ".git")
            repo.git.add(all=True)
            repo.index.commit("Delete not use features")
            origin = repo.remote(name='origin')
            origin.push() 
        except BaseException as err:
            print("exeption : {0}".format(err))
            shutil.rmtree("temp/")
            pass  
    else:
        print("No deletefiles")  
    
    shutil.rmtree("temp/")     
