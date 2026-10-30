import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/dist/transformers.min.js';
env.allowLocalModels = false;
env.backends.onnx.wasm.numThreads = 1;
let transcriber, loadedModel;
const models = {tiny:'Xenova/whisper-tiny',base:'Xenova/whisper-base',small:'Xenova/whisper-small'};
self.onmessage = async ({data}) => {
 try {
  const model=models[data.model] || models.small;
  if(loadedModel!==model){await transcriber?.dispose();transcriber=null;}
  transcriber ??= await pipeline('automatic-speech-recognition', model, {device:'wasm',dtype:'q8',progress_callback:p=>self.postMessage({type:'progress',data:p})});
  loadedModel=model;
  self.postMessage({type:'ready'});
  const result = await transcriber(data.audio,{return_timestamps:'word',chunk_length_s:30,stride_length_s:5,task:'transcribe',...(data.language ? {language:data.language}: {})});
  self.postMessage({type:'result',data:result});
 } catch(e) { self.postMessage({type:'error',message:e.message || String(e)}); }
};
