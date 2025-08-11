/* split kepan.js into jin and lun for human readible format*/
var fs=require("fs")
var Kepan=fs.readFileSync("kepan.js","utf8");
Kepan=JSON.parse(Kepan.substring(13,Kepan.length-2));
var jin=[],lun=[];
for (var i=1;i<Kepan.length;i++) {
	var k=Kepan[i];
	k.f?jin.push(k):lun.push(k);
}

var convert=function(kepan){
	var out=[];
	for (var i=0;i<kepan.length;i++){
		var k=kepan[i]
		out.push(k.l+"\t"+k.t+"\t"+(k.l2||""));
	}
	return out;
}
fs.writeFileSync("jinkepan.txt",convert(jin).join("\n"),"utf8");
fs.writeFileSync("lunkepan.txt",convert(lun).join("\n"),"utf8");
