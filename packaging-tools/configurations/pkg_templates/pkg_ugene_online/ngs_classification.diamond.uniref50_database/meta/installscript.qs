var originalTargetDir = null;

function setTargetDirForMac() {
    if (installer.value("os") == "mac") {
        originalTargetDir = installer.value("TargetDir");
        installer.setValue("TargetDir", "@TargetDir@/Contents/MacOS");
    }
}

function restoreTargetDir() {
    if (installer.value("os") == "mac" && originalTargetDir != null) {
        installer.setValue("TargetDir", originalTargetDir);
        originalTargetDir = null;
    }
}

function Component() {

}

Component.prototype.createOperations = function() {
    setTargetDirForMac();
    component.createOperations();
    restoreTargetDir();
}
