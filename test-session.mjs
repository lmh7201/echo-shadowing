import assert from 'node:assert/strict';
import fs from 'node:fs';
import {bundleName,createSession,parseSession,packSession,unpackSession} from './web/session.js';
import {zipSync,strToU8} from './web/vendor/fflate.js';
const segments=JSON.parse(fs.readFileSync('web/demo.json','utf8'));
const session=createSession(segments,{title:'日本語 <script>',audioFile:'audio.wav',audioMime:'audio/wav'});
const audio=new Uint8Array(fs.readFileSync('web/demo.wav'));
const result=unpackSession(packSession(session,audio));
assert.deepEqual(result.session.segments,segments);assert.deepEqual(result.audio,audio);
assert.equal(result.session.title,'日本語 <script>');
assert.throws(()=>parseSession({...session,version:2}));
assert.throws(()=>parseSession({...session,segments:[{start:NaN,end:1,text:'bad'}]}));
assert.throws(()=>parseSession({...session,segments:[{start:0,end:1,text:'bad',words:[{start:0,end:3,text:'invalid'}]}]}));
assert.throws(()=>unpackSession(zipSync({'session.json':strToU8(JSON.stringify(session))})));
assert.throws(()=>packSession({...session,audioFile:'../secret.wav'},audio));
const when=new Date(2026,10,1,15,30);
assert.equal(bundleName('第12回: Q&A / 질문?',when),'第12回_ Q&A_1101_1530.echo.zip');
assert.equal(bundleName(' ..',when),'echo_1101_1530.echo.zip');
assert.equal(bundleName('😀'.repeat(80),when),'😀'.repeat(10)+'_1101_1530.echo.zip');
if(process.argv[2]){
 const pc=unpackSession(new Uint8Array(fs.readFileSync(process.argv[2])));
 assert.ok(pc.session.segments.length);assert.ok(pc.session.segments.some(s=>s.words?.length));
 console.log('PC-generated ZIP imported with word timing:',pc.session.model,pc.session.segments.length,'segments');
}
console.log('Passed: portable archive round-trip, Japanese text, invalid timing, version, missing audio, path validation.');
