import boto3
from botocore.config import Config
#from boto3.session import Session


class cf:
    cfClient = None
    s3Resource = None
    delStackSet = set()
    stackList = None

    def __init__(self, region):
        my_config = Config(
            region_name = region,
            signature_version = 'v4'
        )

        #session = boto3.Session()

        cf.cfClient = boto3.client('cloudformation', config=my_config)
        cf.stackList = cf.cfClient.list_stacks(StackStatusFilter=['CREATE_FAILED','CREATE_COMPLETE','ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_FAILED','UPDATE_COMPLETE','UPDATE_ROLLBACK_IN_PROGRESS','UPDATE_ROLLBACK_FAILED','UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_ROLLBACK_COMPLETE','REVIEW_IN_PROGRESS','IMPORT_IN_PROGRESS','IMPORT_COMPLETE','IMPORT_ROLLBACK_IN_PROGRESS','IMPORT_ROLLBACK_FAILED','IMPORT_ROLLBACK_COMPLETE'])["StackSummaries"]
        cf.s3Resource = boto3.resource('s3')

    def getDeleteStackList(self, liveBranches, appName):
        tempSet = set()
        stackName = cf.makeStackName(appName)

        if stackName != "":
            for stack in cf.stackList:
                if stackName in stack["StackName"]:
                    tempSet.add(stack["StackName"])

            for branch in liveBranches:
                if stackName + "-" + branch in tempSet:
                    tempSet.remove(stackName + "-" + branch)
                else:
                    continue

        cf.delStackSet = cf.delStackSet.union(tempSet)

    def deleteStack(self):
        for cfStack in cf.delStackSet:
            print("Delete Stack : " + cfStack)
            stackResources = cf.cfClient.list_stack_resources(StackName=cfStack)["StackResourceSummaries"]
            
            try:
                for resource  in stackResources:
                    if resource["ResourceType"] == "AWS::S3::Bucket":
                        if resource["ResourceStatus"] == "DELETE_COMPLETE":
                            print("[ResourceStatus: DELETE_COMPLETE]")
                            print(resource)
                        else:
                            print (cf.s3Resource.Bucket(resource["PhysicalResourceId"]))
                            cf.emptyS3(resource["PhysicalResourceId"])
            except BaseException as err:
                print("exeption : {0}".format(err))
                pass

            cf.cfClient.delete_stack(StackName=cfStack)

        cf.delStackSet = set()


    def deleteAllStackList(self, excluded_stack_names):

        for stack in cf.stackList:
            print ("===============Delete Stack===============")
            print (stack["StackName"])
            stackName_mr = stack["StackName"].split('-')[-1]
            
            if stackName_mr not in excluded_stack_names:
                stackResources = cf.cfClient.list_stack_resources(StackName=stack["StackName"])["StackResourceSummaries"]

                try:
                    for resource  in stackResources:
                        if resource["ResourceType"] == "AWS::S3::Bucket":
                            if resource["ResourceStatus"] == "DELETE_COMPLETE":
                                print("[ResourceStatus: DELETE_COMPLETE]")
                                print(resource)
                            else:
                                print (cf.s3Resource.Bucket(resource["PhysicalResourceId"]))
                                #cf.emptyS3(resource["PhysicalResourceId"])
                        else:
                            continue
                except BaseException as err:
                    print("exeption : {0}".format(err))
                    pass

                #cf.cfClient.delete_stack(StackName=stack)
            else:
                print("pass")
                continue

    def makeStackName(appName):
        if appName == "fe-marketplace":
            return "cf-ue2-dev-naemo-fe-marketplace-feature"
        elif appName == "fe-creator":
            return "cf-ue2-dev-naemo-fe-creator-feature"
        elif appName == "fe-systemadmin":
            return "cf-an2-dev-naemo-fe-systemadmin-feature"
        elif appName == "fe-centralwallet":
            return "cf-an2-dev-naemo-fe-centralwallet-feature"       
        else:
            return ""   

    def emptyS3(bucketName):      
        bucket = cf.s3Resource.Bucket(bucketName)
        bucket.objects.all().delete()

