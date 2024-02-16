import shutil
import os
import json
import xml.etree.ElementTree as ET
import subprocess
from config import folderLocation

logFilePath = folderLocation + "/log.txt"
def maintainLog(logInputList):
    with open(logFilePath , 'a') as file:
        for item in logInputList: file.write(str(item) + '\n')

# Finding all pom.xml files Location in service directory
def findPomXmlLocation(directory):
    try:
        result = subprocess.run(['find', directory, '-name', 'pom.xml', '-type', 'f'], capture_output=True, text=True, check=True)
        outputLines = result.stdout.strip().split('\n')
        return [file.replace(directory, '.') for file in outputLines]
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        return []

def executeMavenCommand(directory , inputDependencyFilePath):
    logList = []
    os.chdir(directory)
    maven_command = "mvn dependency:tree -DoutputType=dot"
    try:
        result = subprocess.run(maven_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        outputLines = result.stdout.split('\n')
        filteredLines = [line for line in outputLines if '>' in line and "[INFO]" in line]
        with open(inputDependencyFilePath, "w") as file: file.write('\n'.join(filteredLines))
        logList.append("Dependency tree successfully saved to " + inputDependencyFilePath)
    except subprocess.CalledProcessError as e:
        logList.append("Error running Maven command:", e)
    maintainLog(logList)

# Taking copy of all pom.xml file and Storing it in PomFile Folder
def copyPomFile(pomFileLocation , acutalPomLocation , pomCopyPath):
    logList = []
    for sourceFile, actualPath in zip(pomFileLocation, acutalPomLocation):
        try:
            destinationPath = sourceFile.split("/")
            fileName = destinationPath[1]
            if len(destinationPath) == 4: fileName += "_" + destinationPath[2]
            if ".xml" != fileName[-4:]: fileName += ".xml"
            shutil.copyfile(actualPath, pomCopyPath + "/" + fileName)
            logList.append("File " + fileName + " copied successfully.")
        except FileNotFoundError: logList.append("File " + fileName + " not found. Please check the file path.")
        except PermissionError: logList.append("File " + fileName + " Permission denied. Please check permissions.")
        except Exception as e: logList.append(f"An error occurred: {e}")
    maintainLog(logList)


def parseFileAndStore(fileName):
    dependencyInfoList = []
    tree = ET.parse(fileName)
    root = tree.getroot()

    namespaces = {'ns': 'http://maven.apache.org/POM/4.0.0'}
    dependencies = root.findall('.//ns:dependencies/ns:dependency', namespaces)

    for dependency in dependencies:
        groupId = dependency.find('ns:groupId', namespaces).text
        artifactId = dependency.find('ns:artifactId', namespaces).text
        versionTag = dependency.find('ns:version', namespaces)
        if versionTag is not None:
            versionText = versionTag.text
            if versionText.startswith('${'):
                propertyName = versionText.strip('${}')
                versionTag = root.find(f'.//ns:properties/ns:{propertyName}', namespaces)
                version = versionTag.text if versionTag is not None else None
            else:
                version = versionText
                propertyName = None
        else:
            version = None
            propertyName = None
        
        scopeTag = dependency.find('ns:scope', namespaces)
        scope = scopeTag.text if scopeTag is not None else None
        exclusions = dependency.findall('ns:exclusions/ns:exclusion', namespaces)
        exclusionList = []
        for exclusion in exclusions:
            exclusionGroupId = exclusion.find('ns:groupId', namespaces).text
            exclusionArtifactId = exclusion.find('ns:artifactId', namespaces).text
            exclusionList.append((exclusionGroupId, exclusionArtifactId))

        if version or propertyName:
            dependencyInfoList.append({
                "Group ID" : groupId,
                "Artifact ID" : artifactId,
                "Version" : version,
                "Property Name" : propertyName,
                "Scope" : scope,
                "Exclusion" : exclusionList
            })
    return dependencyInfoList

# To store the current dependency details in a Json format
def fetchAndStoreDetails(folderPath , pomOutputPath):
    logList = []
    result = {}
    for filename in os.listdir(folderPath):
        if filename.endswith('.xml'):
            filepath = os.path.join(folderPath, filename)
            if os.path.getsize(filepath) > 0:                                       # Check if file is empty
                result[filepath] = parseFileAndStore(filepath)
        
    with open(pomOutputPath , "w") as json_file: json_file.write(json.dumps(result , indent=2))
    logList.append("Pom Json Output --> " + pomOutputPath)
    maintainLog(logList)
    return result


def parseFileAndUpdateVersion(fileName , diffVersion):
    logList = []
    tree = ET.parse(fileName)
    root = tree.getroot()

    namespaces = {'ns': 'http://maven.apache.org/POM/4.0.0'}
    dependencies = root.findall('.//ns:dependencies/ns:dependency', namespaces)

    for dependency in dependencies:
        groupId = dependency.find('ns:groupId', namespaces).text
        artifactId = dependency.find('ns:artifactId', namespaces).text
        key = tuple([groupId , artifactId])

        versionTag = dependency.find('ns:version', namespaces)
        if versionTag is not None:
            versionText = versionTag.text
            if versionText.startswith('${'):
                propertyName = versionText.strip('${}')
                versionTag = root.find(f'.//ns:properties/ns:{propertyName}', namespaces)
                version = versionTag.text if versionTag is not None else None
            else:
                version = versionText
            
            if version and (key in diffVersion) and diffVersion[key]["RequiredVersion"] != version:
                versionTag.text = diffVersion[key]["RequiredVersion"]
                logList.append(fileName + " : Current Version = " + version + " , Updated Version = " + diffVersion[key]["RequiredVersion"] + " , Group ID = " + groupId + " , Atrifact ID = " + artifactId )
                
    tree.write(fileName)                # Write the modified XML back to the file
    maintainLog(logList)
    return "Successfully Updated"

# To parse and update the Version details
def updateVersion(folderPath , diffVersion):
    for filename in os.listdir(folderPath):
        if filename.endswith('.xml'):
            filepath = os.path.join(folderPath, filename)
            if os.path.getsize(filepath) > 0:                                       # Check if file is empty
                parseFileAndUpdateVersion(filepath , diffVersion)
    # diffVersion[tuple(["org.projectlombok" , "lombok"])] = { "Required Version" : "2.0.8" }
    # parseFileAndUpdateVersion("/Users/balamurugan/Desktop/JavaVersion/PomFiles/pom.xml" , diffVersion)