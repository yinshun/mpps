import {nodefs, filesFromPattern, readTextContent, fromObj} from './nodebundle.cjs'
await nodefs
const rootdir='raw/'
const files=filesFromPattern('*.md',rootdir); //列出所有文件
const obj={};

const statbook=fn=>{  //對每個md文件
    const content=readTextContent(rootdir+fn); //讀取內容
    content.replace(/《([^》]+)》/g,(m,bookname)=>{ //找出書名
        if (!obj[bookname])  obj[bookname]=0;
        obj[bookname]++;
    })
}

files.forEach(statbook)
const statobj=fromObj(obj,(a,b)=>[a,b]).sort((a,b)=>b[1]-a[1]);
console.table(statobj)


/*
const statchar=fn=>{  //統計字
    const content=readTextContent(rootdir+fn); //讀取內容
    const chars=content.split(""); //切分成一個個字元
    for (let i=0;i<chars.length;i++){
        const ch=chars[i];
        // if (ch.codePointAt(0)>0x3400) {  Unicode 區段
            if (!obj[ch])  obj[ch]=0;
            obj[ch]++;
        // }
    }
}
*/