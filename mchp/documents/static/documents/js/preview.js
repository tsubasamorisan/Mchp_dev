$(function(){
	// http or https needs to match the site requesting this resource
	ZeroClipboard.config( { swfPath: "http://ajax.cdnjs.com/ajax/libs/zeroclipboard/2.1.5/ZeroClipboard.swf" } );
	var client = new ZeroClipboard(document.getElementById("copy-button") );
});