var installerUpdating = "InstallerUpdating";

function isInstallerUpdatingInProgress() {
    return installer.value(installerUpdating, false) == "true";
}

function setInstallerUpdatingInProgress(isInProgress) {
    installer.setValue(installerUpdating, isInProgress);
}

function Controller() {

}

Controller.prototype.IntroductionPageCallback = function() {
    if (isInstallerUpdatingInProgress()) {
        console.log("Skip introduction page");
        gui.findChild(gui.currentPageWidget(), "UpdaterRadioButton").checked = true;
        gui.clickButton(buttons.NextButton);
    }
}

Controller.prototype.TargetDirectoryPageCallback = function() {
    var widget = gui.currentPageWidget();
    if (widget != null) {
        if (systemInfo.kernelType === "winnt") {
            if (systemInfo.currentCpuArchitecture === "i386") {
                var programFiles = installer.environmentVariable("ProgramFiles");
            }

            if (systemInfo.currentCpuArchitecture === "x86_64") {
                var programFiles = installer.environmentVariable("ProgramW6432");
            }

            if (programFiles != "") {
                installer.setValue("TargetDir", programFiles + "\\Unipro UGENE");
                widget.TargetDirectoryLineEdit.setText(programFiles + "\\Unipro UGENE");
            }
        }
    }
}
