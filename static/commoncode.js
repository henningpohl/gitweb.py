
function makeIdString(str) {	
	str = removeDiacritics(str);
	str = str.replace(/[ \-_]/g, "-");
	return str.replace(/[^a-zA-Z0-9\-]/g, "");
}