import json
import requests
from bs4 import BeautifulSoup
from config import folderLocation

# To Maintain a log File 
logFilePath = folderLocation + "/log.txt"
def maintainLog(logInputList):
    with open(logFilePath , 'a') as file:
        for item in logInputList: file.write(str(item) + '\n')

# Convert the List to Dict , Inorder to perform write operation in Files
def convertToList(dependencyDetails):
    dependencyList = []
    for element in dependencyDetails:
        dependencyInfo = {
            "GroupID" : element[0],
            "ArtifactID": element[1],
            "Version" : dependencyDetails[element]
        }
        dependencyList.append(dependencyInfo)
    return dependencyList

# Get the latest dependency details mentioned in the url and store it in Input Folder
def fetchLatestDependency(url , htmlFilePath , latestDependencyJsonFilePath):
    logList = []
    latestDependencyDetails = {}
    response = requests.get(url)
    if response.status_code == 200:
        with open(htmlFilePath, 'w', encoding='utf-8') as file: file.write(response.text)
        logList.append("HTML response saved --> " + htmlFilePath)
        with open(htmlFilePath, 'r', encoding='utf-8') as htmlFile: htmlContent = htmlFile.read()

        soup = BeautifulSoup(htmlContent, 'html.parser')           # Parse the HTML content using BeautifulSoup
        table = soup.find('table', class_='tableblock')             # Extract relevant data from the HTML table
        if table:
            for row in table.find_all('tr')[1:]:  
                columns = row.find_all('td')
                if len(columns) == 3:
                    groupId = columns[0].text.strip()
                    artifactId = columns[1].text.strip()
                    version = columns[2].text.strip()
                    latestDependencyDetails[tuple([groupId , artifactId])] = version

        latestDependencyDetailsList = convertToList(latestDependencyDetails)
        with open(latestDependencyJsonFilePath, 'w', encoding='utf-8') as jsonFile: jsonFile.write(json.dumps(latestDependencyDetailsList, indent=2))
        logList.append("Dependency details saved --> " + latestDependencyJsonFilePath)
    else: 
        logList.append("Failed to fetch the URL. Status code:" + response.status_code)

    maintainLog(logList)
    return latestDependencyDetails

# From the Maven Tree result file , gather all the dependency details
def extractOurDependency(filePath , ourDependencyPath):
    logList = []
    dependencyDetails = {}
    with open(filePath, 'r') as file:
        for line in file:
            parts = line.strip().split("->")
            if len(parts) == 2:
                dependency1 = parts[0].strip()
                dependency2 = parts[1].strip().split(";")

                dependencyParts = dependency1.strip().split(":")
                if len(dependencyParts) >= 3:
                    groupId = dependencyParts[0].strip().split("\t")[1]
                    artifactId = dependencyParts[1].strip()
                    version = dependencyParts[3].strip()
                    if version[-1] == '"': version = version[:-1]
                    dependencyDetails[tuple([groupId[1:] , artifactId])] = version
                else: print(dependency1)
                
                dependencyParts = dependency2[0].strip().split(":")
                if len(dependencyParts) >= 3:
                    groupId = dependencyParts[0].strip()
                    artifactId = dependencyParts[1].strip()
                    version = dependencyParts[3].strip()
                    dependencyDetails[tuple([groupId[1:] , artifactId])] = version
                else: print(dependency2)
    
    ourDependencyDetailsList = convertToList(dependencyDetails)
    with open(ourDependencyPath , "w") as jsonFile: jsonFile.write(json.dumps(ourDependencyDetailsList , indent=2))
    logList.append("Our Dependency Details stored --> " + ourDependencyPath)

    maintainLog(logList)
    return dependencyDetails

# Differentiate the dependency based on the comparision with current and new version
def categoriesDependency(ourDependencyDetails , latestDependencyDetails , matchedDependencyPath , missingDependencyPath , diffVersionPath):
    logList = []
    missingDependency , diffVersion , matchedDependency = [] , [] , []
    for element in ourDependencyDetails:
        if element not in latestDependencyDetails:
            missingDependency.append({
                "GroupID" : element[0],
                "ArtifactID" : element[1],
                "Version" : ourDependencyDetails[element]
            })
        elif latestDependencyDetails[element] != ourDependencyDetails[element]:
            diffVersion.append({
                "GroupID" : element[0],
                "ArtifactID" : element[1],
                "OurVersion" : ourDependencyDetails[element],
                "RequiredVersion" : latestDependencyDetails[element] 
            })
        else:
            matchedDependency.append({
                "GroupID" : element[0],
                "ArtifactID" : element[1],
                "Version" : ourDependencyDetails[element]
            })

    with open(matchedDependencyPath , "w") as jsonFile: jsonFile.write(json.dumps(matchedDependency , indent=2))
    logList.append("Macthed Dependency saved --> " + matchedDependencyPath)
    with open(missingDependencyPath , "w") as jsonFile: jsonFile.write(json.dumps(missingDependency , indent=2))
    logList.append("Missing Dependency saved --> " + missingDependencyPath)
    with open(diffVersionPath , "w") as jsonFile: jsonFile.write(json.dumps(diffVersion , indent=2))
    logList.append("Version Mismatch saved --> " + diffVersionPath)

    maintainLog(logList)
    return [customizeListToDict(missingDependency , "missingDependency"), customizeListToDict(diffVersion , "diffVersion"), customizeListToDict(matchedDependency , "matchedDependency")]

# Customise the List to Dict , For easy access 
def customizeListToDict(inputList , listName):
    result = {}
    if listName == "diffVersion":
        for element in inputList:
            result[tuple([element["GroupID"] , element["ArtifactID"]])] = {
                "OurVersion" : element["OurVersion"],
                "RequiredVersion" : element["RequiredVersion"]
            }
    else:
        for element in inputList:
            result[tuple([element["GroupID"] , element["ArtifactID"]])] = { "Version" : element["Version"] }
    return result    
    