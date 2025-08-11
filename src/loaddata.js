import {nodefs,readTextContent,unescapeTemplateString} from '../nodebundle.cjs'
await nodefs
const indir='./raw2017/';

const loadScript=fn=>{
    const raw=readTextContent(fn);
    const at=raw.indexOf('(`');
    const at2=raw.lastIndexOf('`)');
    let s=unescapeTemplateString(raw.slice(at+2,at2));
    return s;
}
const loadObject=fn=>{
    const raw=readTextContent(fn);
    const at=raw.indexOf('cb(');
    const at2=raw.lastIndexOf(')');
    let s=JSON.parse(raw.slice(at+3,at2));
    return s;
}
const lun=loadScript(indir+'lun.js')
const jin=loadScript(indir+'jin.js')
const kepan=loadObject(indir+'kepan.js')
const ndef0=loadObject(indir+'ndef0.js')
const ndef1=loadObject(indir+'ndef1.js')
const ndef2=loadObject(indir+'ndef2.js')
const ndef3=loadObject(indir+'ndef3.js')
const ndef4=loadObject(indir+'ndef4.js')
const ndef5=loadObject(indir+'ndef5.js')
const ndef6=loadObject(indir+'ndef6.js')
const ndef7=loadObject(indir+'ndef7.js')
const ndef8=loadObject(indir+'ndef8.js')
const ndef9=loadObject(indir+'ndef9.js')

export {lun,jin,kepan,ndef0,ndef1,ndef2,ndef3,ndef4,ndef5,ndef6,ndef7,ndef8,ndef9}