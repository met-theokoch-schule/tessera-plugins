import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const context=vm.createContext({});
vm.runInContext(script,context);
const crop=(...args)=>JSON.parse(JSON.stringify(context.squareCrop(...args)));

test('Portrait: largest square moves only vertically',()=>{
 assert.deepEqual(crop(600,1000),{size:600,x:0,y:200,offset:200,maxOffset:400,axis:'y'});
 assert.equal(crop(600,1000,400).y,400);
 assert.equal(crop(600,1000,-50).y,0);
 assert.equal(crop(600,1000,10000).y,400);
});
test('Landscape: largest square moves only horizontally',()=>{
 assert.deepEqual(crop(1000,600),{size:600,x:200,y:0,offset:200,maxOffset:400,axis:'x'});
 assert.equal(crop(1000,600,400).x,400);
});
test('Already square: no movement or upscaling',()=>{
 assert.deepEqual(crop(900,900,200),{size:900,x:0,y:0,offset:0,maxOffset:0,axis:'y'});
});
test('Odd sizes and fractional drags stay inside source pixels',()=>{
 for(const [w,h] of [[1,7],[7,1],[317,1200],[1901,643],[24,24],[12000,5000]]){
  for(const offset of [-100,0,.5,13.7,99999]){
   const c=crop(w,h,offset);
   assert.ok(Number.isInteger(c.x)&&Number.isInteger(c.y));
   assert.ok(c.x>=0&&c.y>=0&&c.x+c.size<=w&&c.y+c.size<=h);
   assert.equal(c.size,Math.min(w,h));
  }
 }
});
test('Invalid image dimensions are rejected',()=>{
 for(const [w,h] of [[0,10],[-1,10],[10,0],[NaN,2],[10.2,4],[4,Infinity]])assert.throws(()=>crop(w,h));
});
test('Display fitting preserves aspect ratio and uses available space',()=>{
 for(const [w,h] of [[600,1000],[1000,600],[900,900]]){
  const f=context.fitImage(w,h,680,390);
  assert.ok(f.width<=680+.001&&f.height<=390+.001);
  assert.ok(Math.abs(f.width/f.height-w/h)<.000001);
  assert.ok(Math.abs(f.width-680)<.001||Math.abs(f.height-390)<.001);
 }
});
test('Keyboard follows movement axis, clamps edges and supports Home/End',()=>{
 assert.equal(context.moveByKey('ArrowRight',200,400,'x'),204);
 assert.equal(context.moveByKey('ArrowRight',200,400,'x',true),240);
 assert.equal(context.moveByKey('ArrowDown',200,400,'x'),null);
 assert.equal(context.moveByKey('ArrowDown',200,400,'y'),204);
 assert.equal(context.moveByKey('Home',200,400,'y'),0);
 assert.equal(context.moveByKey('End',200,400,'y'),400);
 assert.equal(context.moveByKey('ArrowRight',399,400,'x',true),400);
});
test('Download name preserves readable titles and replaces the extension',()=>{
 assert.equal(context.coverFilename('Conni Weihnachten.jpeg'),'Conni Weihnachten-cover.jpg');
 assert.equal(context.coverFilename('hörspiel.png'),'hörspiel-cover.jpg');
 assert.equal(context.coverFilename('a/b\\c.webp'),'a_b_c-cover.jpg');
 assert.equal(context.coverFilename('.jpg'),'bild-cover.jpg');
});
test('Standalone page contains no dependencies, uploads or remote assets',()=>{
 assert.ok(!/<script[^>]+src=/i.test(html));
 assert.ok(!/<link[^>]+href=/i.test(html));
 assert.ok(!/\bfetch\s*\(|XMLHttpRequest|FormData\s*\(/.test(script));
 assert.ok(!/https?:\/\//.test(html));
});
