function Component() {
	var visible = systemInfo.currentCpuArchitecture === 'x86_64'
		&& (systemInfo.kernelType === 'linux' || systemInfo.kernelType === 'darwin');

	installer.componentByName("ngs_classification").setValue("Virtual", '' + !visible); // Virtual == hidden
}
/*
Component.prototype.createOperations = function() {
	try {
		// call the base create operations function
		//component.createOperations();
		//component.addOperation("Download", "ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz");
	} catch (e) {
		print(e);
	}
}
*/

