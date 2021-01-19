function Component()
{
}

Component.prototype.createOperations = function()
{
    component.createOperations();
    createShortcuts();
}
function createShortcuts()
{
    if (systemInfo.kernelType === "winnt") {
        var component_root_path = installer.value("TargetDir");
        component_root_path = component_root_path.replace(/\//g, "\\");

        // Crate shortcut
        component.addOperation( "CreateShortcut",
                                component_root_path + "/tools/",
                                "@StartMenuDir@/Tools.lnk");
    }
}
