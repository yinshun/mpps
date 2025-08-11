import {readTextContent,nodefs,writeChanged,unescapeTemplateString} from './nodebundle.cjs'
await nodefs;
import  {lun,jin,kepan,ndef0,ndef1,ndef2,ndef3,ndef4,ndef5,ndef6,ndef7,ndef8,ndef9} from './src/loaddata.js'
const converttag=content=>{
    content=content.replace(/\ufeff/g,'')
    .replace(/~(\d+)/g,'^pg$1')
    .replace(/#(\d+\.\d+)/g,'^f$1')
    .replace(/@t([\dpabcd]+)/g,'^taisho$1')
    .replace(/@y([\da-zA-Z]+)/g,(m,m1)=>'^ys#'+m1.toLowerCase())
    .replace(/\{k/g,'^kai[')
    .replace(/\k}/g,']')
    .replace(/}/g,']')
    .replace(/\{/g,'^b[')
    const lines=content.split('\n');
    for (let j=0;j<lines.length;j++) {
        const line=lines[j];
        const m=line.match(/%(\d+\.\d+)/);
        if (m){
            lines[j]='^kp'+m[1]
        }
    }
    return lines.join('\n').trim()
}
const splitjin=()=>{
    const obj={};
    const D=jin.split(/\^(\d+\.\d+)/);
    D.shift();
    for (let i=0;i<D.length /2 ;i++){
        const page=D[i*2];
        const content=converttag(D[i*2+1]);
        obj[page]=content;
    }
    return obj
}
const out=[];
const notes=[];
const dumpndef=defs=>{
    for (let i in defs) {
        notes.push(i+'\t'+converttag(defs[i]));
    }
}

const luns=converttag(lun).split('\n');
const jins=splitjin();


for (let i=0;i<luns.length;i++) {
    const line=luns[i];
    const m=line.match(/\^(\d+\.\d+)/);
    // console.log(line)
    if (m) {
        const j=jins[m[1]];
        out.push('^jin'+m[1] +' '+j);
    } else {
        out.push(line);
    }
}
dumpndef(ndef0)
dumpndef(ndef1)
dumpndef(ndef2)
dumpndef(ndef3)
dumpndef(ndef4)
dumpndef(ndef5)
dumpndef(ndef6)
dumpndef(ndef7)
dumpndef(ndef8)
dumpndef(ndef9)
writeChanged('mpps.off',out.join('\n'),true)
writeChanged('notes.off',notes.join('\n'),true)

