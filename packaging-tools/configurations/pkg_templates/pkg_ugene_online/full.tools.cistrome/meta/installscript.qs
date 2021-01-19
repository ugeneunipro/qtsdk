function Component()
{
    //
    // Hide/select packages based on architecture
    //
    // Marking a component as "Virtual" will hide it in the UI.
    // Marking a component with "Default" will check it.
    //
    console.log("CPU Architecture: " +  systemInfo.currentCpuArchitecture);

    installer.componentByName("full.tools.cistrome").setValue("Virtual", "true");
    installer.componentByName("full.tools.cistrome").setValue("Default", "false");

    if (systemInfo.currentCpuArchitecture === "x86_64") {
        installer.componentByName("full.tools.cistrome").setValue("Virtual", "false");
        installer.componentByName("full.tools.cistrome").setValue("Default", "true");
    }
}
