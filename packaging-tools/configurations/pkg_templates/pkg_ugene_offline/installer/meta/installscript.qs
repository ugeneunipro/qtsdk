var INSTALLER_UPDATING = "InstallerUpdating";
var IS_UPDATER = "IsUpdater";

function isInstallerUpdatingInProgress() {
    return installer.value(INSTALLER_UPDATING, false) == "true";
}

function setInstallerUpdatingInProgress(isInProgress) {
    installer.setValue(INSTALLER_UPDATING, isInProgress);
}

function finalizeInstallerUpdating() {
    console.log("Installer update finalization");

    if (installer.value(IS_UPDATER, false) == "true") {
        installer.setValue(IS_UPDATER, false);
    }

    setInstallerUpdatingInProgress(false);
}

function getInstallerVersion() {
    console.log("installer.value(\"Version\") == " + installer.value("Version"));
    console.log("component.value(\"Name\") == " + component.value("Name"));
    console.log("component.value(\"Version\") == " + component.value("Version"));
    // There should be a method to get the installer version from scripts
    if (installer.value("Version") == "1.23.0") {
        return "2.0.1";
    } else if (installer.value("Version") == "1.30.0") {
        return "3.0.3.1";
    } else if (installer.value("Version") == "1.35.0") {
        return "3.2";
    } else if (installer.value("Version") == "35.1") {
        return "3.2.3.1";
    } else {
        return "";
    }
}

function isUpdateNecessary() {
    return installer.versionMatches(getInstallerVersion(), "<" + component.value("Version"));
}

function cancelInstallation(message) {
    installer.setDefaultPageVisible(QInstaller.Introduction, false);
    installer.setDefaultPageVisible(QInstaller.TargetDirectory, false); 
    installer.setDefaultPageVisible(QInstaller.ComponentSelection, false);
    installer.setDefaultPageVisible(QInstaller.LicenseCheck, false);
    installer.setDefaultPageVisible(QInstaller.PerformInstallation, false);
    installer.setDefaultPageVisible(QInstaller.StartMenuSelection, false);
    installer.setDefaultPageVisible(QInstaller.ReadyForInstallation, false);

    var finishPage = gui.pageById(QInstaller.InstallationFinished);
    if (finishPage != null) {
        finishPage.entered.connect(this, Component.prototype.onInstallationFinishedPageEnter);
    }

    installer.setValue("FinishedText", "<font color='red'>" + message + "</font>");
}

function Component() {
    if (isInstallerUpdatingInProgress()) {
        finalizeInstallerUpdating();
    } else {
        if (isUpdateNecessary() && installer.isInstaller()) {
            cancelInstallation("The UGENE installer version is outdated. Please download an actual version from the <a href='http://ugene.net/download.html'>UGENE downloads page</a>.");
            return;
        }

        installer.finishedCalculateComponentsToInstall.connect(this, Component.prototype.onFinishedCalculateComponentsToInstall);
        installer.installationFinished.connect(this, Component.prototype.onInstallationFinished);
        installer.installationInterrupted.connect(this, Component.prototype.onInstallationInterrupted);

        var page = gui.pageById(QInstaller.PerformInstallation);
        if (page != null) {
            page.entered.connect(this, Component.prototype.onPerformInstallationPageEnter);
        }
    }
}

Component.prototype.onInstallationFinishedPageEnter = function() {
    if (installer.value("FinishText", "").isEmpty) {
        return;
    }

    var finishPage = gui.pageById(QInstaller.InstallationFinished);
    if (finishPage != null) {
        finishPage.RunItCheckBox.checked = false;
        finishPage.RunItCheckBox.visible = false;
        finishPage.MessageLabel.openExternalLinks = true;
    }
}

Component.prototype.onPerformInstallationPageEnter = function() {
    if (!isInstallerUpdatingInProgress()) {
        return;
    }

    var page = gui.pageById(QInstaller.PerformInstallation);
    if (page != null) {
        page.title = "Updating UGENE Maintenance Tool";
    }
}

Component.prototype.onFinishedCalculateComponentsToInstall = function() {
    if (isInstallerUpdatingInProgress()) {
        return;
    }

    if (isUpdateNecessary()) {
        console.log("Installer has to be updated, begin updating immediately...");

        setInstallerUpdatingInProgress(true);

        // Do not disturb the user, just update the installer
        installer.setDefaultPageVisible(QInstaller.Introduction, false);
        installer.setDefaultPageVisible(QInstaller.TargetDirectory, false);
        installer.setDefaultPageVisible(QInstaller.ComponentSelection, false);
        installer.setDefaultPageVisible(QInstaller.LicenseCheck, false);
        installer.setDefaultPageVisible(QInstaller.StartMenuSelection, false);
        installer.setDefaultPageVisible(QInstaller.ReadyForInstallation, false);
        installer.setDefaultPageVisible(QInstaller.InstallationFinished, false);

        if (installer.isUpdater()) {
            installer.setValue(IS_UPDATER, true);
        }
    } else {
        console.log("Installer version is up-to-date");
        if (installer.isInstaller()) {
            for (var i = 0; i < component.archives.length; i++) {
                component.removeDownloadableArchive(component.archives[i]);
            }
        }
    }
}

Component.prototype.createOperations = function() {
    component.createOperations();

    var oldResourceFilePath = "@TargetDir@/setup.app/Contents/Resources/installer.dat";
    var normalizedOldResourceFilePath = oldResourceFilePath.replace(/@TargetDir@/, installer.value("TargetDir"));

    if (installer.value("os") == "mac" && getInstallerVersion() == "2.0.1" && isInstallerUpdatingInProgress() && installer.fileExists(normalizedOldResourceFilePath)) {
        // A workaround for installer v2.0.1 on mac: it can't to update itself if 'installer.dat' exists
        console.log("Installer version is 2.0.1, using a workaround for installer update.");
        component.addOperation("SimpleMoveFile", normalizedOldResourceFilePath, normalizedOldResourceFilePath + ".bak");
    }
}

function getNewInstallerbaseBinaryPath() {
    var os = installer.value("os");
    if (os == "mac") {
        return "@TargetDir@/UgeneInstaller";
    } else if (os == "x11") {
        return "@TargetDir@/UgeneInstaller";
    } else if (os == "win") {
        return "@TargetDir@/UgeneInstaller.exe";
    }
    return null;
}

Component.prototype.onInstallationFinished = function() {
    if (isInstallerUpdatingInProgress() && (component.updateRequested() || component.installationRequested())) {
        var newInstallerbaseBinaryPath = getNewInstallerbaseBinaryPath();
        if (newInstallerbaseBinaryPath != null) {
            installer.setInstallerBaseBinary(newInstallerbaseBinaryPath);
        }

        // update resource file if exists in the archive
        var updateResourceFilePath = "@TargetDir@/update.rcc";
        var normalizedUpdateResourceFilePath = updateResourceFilePath.replace(/@TargetDir@/, installer.value("TargetDir"));
        if (installer.fileExists(normalizedUpdateResourceFilePath)) {
            console.log("Resource update file exists");
            print("Updating resource file: " + normalizedUpdateResourceFilePath);
            installer.setValue("DefaultResourceReplacement", normalizedUpdateResourceFilePath);
        } else {
            console.log("Resource update file doesn't exist");
        }

        if (installer.fileExists(newInstallerbaseBinaryPath)) {
            if (installer.performOperation("Delete", newInstallerbaseBinaryPath)) {
                console.log("Installation was finished, the UgeneInstaller deleted itself and exited.");
            }
        }
    }
}

Component.prototype.onInstallationInterrupted = function() {
    installer.setDefaultPageVisible(QInstaller.InstallationFinished, true);
    setInstallerUpdatingInProgress(false);
}
