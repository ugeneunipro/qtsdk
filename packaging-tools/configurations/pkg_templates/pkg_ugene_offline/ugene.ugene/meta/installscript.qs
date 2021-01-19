function Component() {

}

Component.prototype.createOperations = function() {
    component.createOperations();

    if (installer.isUpdater() && component.updateRequested()) {
        component.addOperation("SendStatistics", "http://ugene.net/installer_reports_dest.php");
    }

    if (systemInfo.kernelType === "winnt") {
        installer.performOperation("Delete", installer.value("TargetDir") + "/ugene.exe");
    }
}
