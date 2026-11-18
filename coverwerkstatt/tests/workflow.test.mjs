// Execute the actual page/controller with small DOM/image/canvas doubles.
// These tests validate interactions and export coordinates, not browser pixels.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(){
 const elements=new Map(),urls=new Map(),revoked=[],exports=[],downloads=[];let sequence=0;
 class Element {
  constructor(id=''){this.id=id;this.hidden=false;this.disabled=false;this.style={};this.listeners={};this.attributes={};this.textContent='';this.value='';this.files=[];this.classList={toggle(){},add(){},remove(){}};}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  setAttribute(key,value){this.attributes[key]=value;}
  async emit(type,extra={}){const event={preventDefault(){},target:this,...extra};for(const fn of this.listeners[type]??[])await fn(event);await flush();}
  getBoundingClientRect(){return{width:600,height:390,left:0,top:0};}
  contains(target){return target===this;}
  focus(){}
  setPointerCapture(id){this.pointer=id;}
  append(){}
  click(){if(this.download)downloads.push({filename:this.download,url:this.href});}
  remove(){}
  getContext(){return{fillRect(){},drawImage:(...args)=>{this.drawArgs=args;}};}
  toBlob(callback,type,quality){exports.push({canvas:this,type,quality});callback({type,size:100});}
 }
 const get=id=>{if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);};
 class ImageDouble {
  set src(value){this.url=value;const file=urls.get(value);this.naturalWidth=file.width;this.naturalHeight=file.height;this.file=file;}
  decode(){return this.file.corrupt?Promise.reject(new DOMException('decode','EncodingError')):this.file.wait??Promise.resolve();}
 }
 const document=new Element();document.getElementById=get;document.body=new Element();document.createElement=()=>new Element();
 const context=vm.createContext({document,window:new Element(),Image:ImageDouble,DOMException,
  URL:{createObjectURL:value=>{const url='blob:test-'+(++sequence);urls.set(url,value);return url;},revokeObjectURL:url=>revoked.push(url)},
  ResizeObserver:class{observe(){}},requestAnimationFrame:fn=>{queueMicrotask(fn);return ++sequence;},setTimeout(){}});
 vm.runInContext(script,context);
 async function load(file){get('file-input').files=[file];await get('file-input').emit('change');await flush();}
 return{get,load,exports,downloads,revoked};
}
const photo=(extra={})=>({name:'Conni.png',type:'image/png',size:100,width:1200,height:600,...extra});

test('Load, move range and export only the selected square at source resolution',async()=>{
 const f=fixture();await f.load(photo());
 assert.equal(f.get('download').disabled,false);
 assert.equal(f.get('output-size').textContent,'600 × 600 px');
 assert.equal(f.get('position').value,'300');
 f.get('position').value='600';await f.get('position').emit('input');
 await f.get('download').emit('click');
 const {canvas,type}=f.exports[0];
 assert.equal(canvas.width,600);assert.equal(canvas.height,600);assert.equal(type,'image/jpeg');
 assert.deepEqual(Array.from(canvas.drawArgs.slice(1)),[600,0,600,600,0,0,600,600]);
 assert.equal(f.downloads[0].filename,'Conni-cover.jpg');
});
test('Portrait keyboard movement affects y, then centre restores the middle',async()=>{
 const f=fixture();await f.load(photo({width:600,height:1200}));
 await f.get('selection').emit('keydown',{key:'End'});
 assert.equal(f.get('position').value,'600');
 await f.get('download').emit('click');
 assert.deepEqual(Array.from(f.exports[0].canvas.drawArgs.slice(1)),[0,600,600,600,0,0,600,600]);
 await f.get('center').emit('click');assert.equal(f.get('position').value,'300');
});
test('Pointer dragging is limited to the longer axis and clamps to image edges',async()=>{
 const f=fixture();await f.load(photo());
 await f.get('image-area').emit('pointerdown',{target:f.get('selection'),isPrimary:true,button:0,pointerId:1,clientX:200,clientY:200});
 await f.get('image-area').emit('pointermove',{pointerId:1,clientX:2000,clientY:-900});
 await f.get('image-area').emit('pointerup',{pointerId:1});
 assert.equal(f.get('position').value,'600');
 await f.get('download').emit('click');assert.equal(f.exports[0].canvas.drawArgs[2],0);
});
test('Square source disables movement and exports the complete square',async()=>{
 const f=fixture();await f.load(photo({width:900,height:900}));
 assert.equal(f.get('position').disabled,true);assert.equal(f.get('center').disabled,true);
 await f.get('download').emit('click');
 assert.deepEqual(Array.from(f.exports[0].canvas.drawArgs.slice(1)),[0,0,900,900,0,0,900,900]);
});
test('Unreadable images show a friendly error and retain the usable previous image',async()=>{
 const f=fixture();await f.load(photo());await f.load(photo({corrupt:true}));
 assert.equal(f.get('download').disabled,false);
 assert.match(f.get('message').textContent,/Browser nicht öffnen/);
 assert.equal(f.get('output-size').textContent,'600 × 600 px');
});
test('A slower previous load cannot replace a more recent file',async()=>{
 const f=fixture();let resolve;const wait=new Promise(done=>{resolve=done;});
 await f.load(photo({name:'old.png',wait}));await f.load(photo({name:'new.png',width:500,height:700}));
 resolve();await flush();await flush();
 assert.equal(f.get('file-info').textContent,'new.png');
 assert.equal(f.get('output-size').textContent,'500 × 500 px');
 assert.equal(f.get('download').disabled,false);
 assert.ok(f.revoked.length>0);
});
test('Invalid drop during a pending load does not leave controls permanently busy',async()=>{
 const f=fixture();let resolve;const wait=new Promise(done=>{resolve=done;});
 await f.load(photo({wait}));await f.load(photo({name:'test.txt',type:'text/plain'}));
 resolve();await flush();await flush();
 assert.equal(f.get('download').disabled,false);assert.equal(f.get('workspace').attributes['aria-busy'],'false');
});
