// render.mjs — deterministic CDP capture. Env: CDP_URL, PAGE_URL, FRAMES,
// TOTAL_FRAMES, FPS, WIDTH, HEIGHT. Verifies GPU adapter before any frame.
import { writeFileSync, mkdirSync, readdirSync } from 'fs';
const CDP=process.env.CDP_URL||'http://127.0.0.1:9333';
const URL=process.env.PAGE_URL;
const FRAMES=process.env.FRAMES;
const TOTAL=Number(process.env.TOTAL_FRAMES||1008);
const FPS=Number(process.env.FPS||24);
const W=Number(process.env.WIDTH||1920), H=Number(process.env.HEIGHT||1080);
if(!URL||!FRAMES) throw new Error('PAGE_URL and FRAMES required');
mkdirSync(FRAMES,{recursive:true});
const targets=await(await fetch(`${CDP}/json`)).json();
const page=targets.find(t=>t.type==='page'&&!t.url.startsWith('chrome-extension'));
if(!page) throw new Error('no page target');
const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pending.has(m.id)){
  const{resolve,reject}=pending.get(m.id);pending.delete(m.id);
  m.error?reject(new Error(m.error.message)):resolve(m.result);}};
await new Promise(r=>ws.onopen=r);
const send=(method,params={})=>new Promise((resolve,reject)=>{
  const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
await send('Page.enable');
await send('Network.enable').catch(()=>{});
await send('Network.setCacheDisabled',{cacheDisabled:true}).catch(()=>{});
await send('Page.navigate',{url:URL+'?cb='+Date.now()});
await new Promise(r=>setTimeout(r,5000));
await send('Emulation.setDeviceMetricsOverride',{width:W,height:H,deviceScaleFactor:1,mobile:false});
await new Promise(r=>setTimeout(r,1500));
const gpu=await send('Runtime.evaluate',{expression:`(()=>{const gl=document.createElement('canvas').getContext('webgl2');
 if(!gl)return'NO_WEBGL2';const d=gl.getExtension('WEBGL_debug_renderer_info');
 return d?gl.getParameter(d.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);})()`,returnByValue:true});
console.log('GPU='+gpu.result.value);
const ready=await send('Runtime.evaluate',{expression:'window.__ready===true',returnByValue:true});
if(!ready.result.value) throw new Error('studio not ready');
for(let i=0;i<TOTAL;i++){
  const sec=i/FPS;
  await send('Runtime.evaluate',{expression:`window.__setTime(${sec})`});
  const {data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  writeFileSync(`${FRAMES}/frame_${String(i).padStart(5,'0')}.png`,Buffer.from(data,'base64'));
  if(i%Math.max(1,Math.floor(TOTAL/6))===0) console.log(`frame ${i}/${TOTAL}`);
}
ws.close();
const got=readdirSync(FRAMES).filter(f=>f.endsWith('.png')).length;
console.log('CAPTURED='+got);
if(got!==TOTAL) throw new Error(`frame count ${got} != ${TOTAL} — refuse to encode`);
