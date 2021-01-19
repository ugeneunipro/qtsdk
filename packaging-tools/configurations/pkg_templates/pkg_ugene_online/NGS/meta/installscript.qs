function Component()
{
    //
    // Hide/select packages based on architecture
    //
    // Marking a component as "Virtual" will hide it in the UI.
    // Marking a component with "Default" will check it.
    //
    console.log("CPU Architecture: " +  systemInfo.currentCpuArchitecture);

    installer.componentByName("NGS.RScript").setValue("Virtual", "true");
    installer.componentByName("NGS.cistrome").setValue("Virtual", "true");
    installer.componentByName("NGS").setValue("Virtual", "true");

    if ( systemInfo.currentCpuArchitecture === "x86_64") {
        installer.componentByName("NGS.RScript").setValue("Virtual", "false");
        installer.componentByName("NGS.cistrome").setValue("Virtual", "false");
        installer.componentByName("NGS").setValue("Virtual", "false");
    }
}
