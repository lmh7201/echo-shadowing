import {zipSync,unzipSync,strToU8,strFromU8} from './vendor/fflate.js';
const MAX_AUDIO=180*1024*1024,MAX_JSON=10*1024*1024;
export function parseSession(value){
 const x=typeof value==='string'?JSON.parse(value.replace(/^\uFEFF/,'')):value;
 if(x?.format!=='echo-session'||x.version!==1||!Array.isArray(x.segments)||!x.segments.length||x.segments.length>50000)throw Error('지원되는 Echo 연습 파일이 아닙니다.');
 const time=n=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<604800;
 let previous=-1,wordCount=0;
 const segments=x.segments.map(s=>{
  if(!time(s.start)||!time(s.end)||s.end<=s.start||s.start<previous||typeof s.text!=='string'||s.text.length>20000)throw Error('자막의 문장 시간이나 내용이 잘못되었습니다.');
  previous=s.start;
  const out={start:s.start,end:s.end,text:s.text};
  if(s.words!==undefined){if(!Array.isArray(s.words))throw Error('단어 정보 형식이 잘못되었습니다.');let last=s.start-.5;out.words=s.words.map(w=>{wordCount++;if(wordCount>300000||!time(w.start)||!time(w.end)||w.end<w.start||w.start<last||w.start<s.start-.5||w.end>s.end+.5||typeof w.text!=='string'||w.text.length>2000)throw Error('단어의 시간이나 내용이 잘못되었습니다.');last=w.start;return {start:w.start,end:w.end,text:w.text}})}
  return out;
 });
 return {format:'echo-session',version:1,title:typeof x.title==='string'?x.title.slice(0,300):'가져온 연습',audioFile:typeof x.audioFile==='string'?x.audioFile:'',audioMime:typeof x.audioMime==='string'?x.audioMime:'',model:typeof x.model==='string'?x.model:'',language:typeof x.language==='string'?x.language:'',preview:!!x.preview,segments};
}
export function createSession(segments,metadata={}){return parseSession({...metadata,format:'echo-session',version:1,segments})}
export function packSession(session,audio){
 if(audio.length>MAX_AUDIO)throw Error('연습 파일은 음성 180MB 이하에서 저장할 수 있어요. 자막 JSON과 원본 음성을 따로 옮겨주세요.');
 const name=session.audioFile;
 if(!/^audio\.[a-z0-9]{1,8}$/i.test(name))throw Error('음성 파일 이름이 잘못되었습니다.');
 return zipSync({'session.json':[strToU8(JSON.stringify(session)),{level:6}],[name]:[audio,{level:0}]});
}
export function unpackSession(bytes){
 if(bytes.length>MAX_AUDIO+MAX_JSON)throw Error('연습 파일이 너무 큽니다. 음성과 자막 JSON을 따로 가져와 주세요.');
 let total=0;
 const files=unzipSync(bytes,{filter:f=>{if(f.name!=='session.json'&&!/^audio\.[a-z0-9]{1,8}$/i.test(f.name))return false;const limit=f.name==='session.json'?MAX_JSON:MAX_AUDIO;if(f.originalSize>limit||(total+=f.originalSize)>MAX_AUDIO+MAX_JSON)throw Error('압축을 푼 연습 파일이 너무 큽니다.');return true}});
 if(!files['session.json'])throw Error('연습 파일 안에 session.json이 없습니다.');
 const session=parseSession(strFromU8(files['session.json']));
 if(!/^audio\.[a-z0-9]{1,8}$/i.test(session.audioFile)||!files[session.audioFile])throw Error('연습 파일 안에 음성이 없습니다.');
 return {session,audio:files[session.audioFile]};
}
