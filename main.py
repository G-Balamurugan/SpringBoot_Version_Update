import json
from ExtractDetails import fetchLatestDependency , convertToList , extractOurDependency , categoriesDependency 
from PomMain import copyPomFile , fetchAndStoreDetails , updateVersion , findPomXmlLocation , executeMavenCommand
import config

with open(config.logFilePath, 'w') as file: pass                       # To empty the Log File initially

# To fetch Maven Tree and store it in .txt File 
executeMavenCommand(config.pwdForService , config.inputDependencyFilePath)

# To retrieve all Locations of pom.xml 
pomFileLocation = findPomXmlLocation(config.pwdForService)
acutalPomLocation = [config.pwdForService + element[1:] for element in pomFileLocation]

latestDependencyDetails = fetchLatestDependency(config.url , config.htmlFilePath , config.latestDependencyJsonFilePath)
ourDependencyDetails = extractOurDependency(config.inputDependencyFilePath , config.ourDependencyPath)
missingDependency , diffVersion , matchedDependency = categoriesDependency(ourDependencyDetails , latestDependencyDetails , config.matchedDependencyPath , config.missingDependencyPath , config.diffVersionPath)

copyPomFile(pomFileLocation , acutalPomLocation , config.pomCopyPath)        # Copying each pom.xml File and storing it in 'pomCopyPath' Folder
dependencyInfo = fetchAndStoreDetails(config.pomCopyPath , config.pomOutputPath)      # To fetch all pom.xml File details and store it as Dict 
updateVersion(config.pomCopyPath , diffVersion)                              # To update the Versions in each pom.xml file

print("\n Execution Completed ... \n")

