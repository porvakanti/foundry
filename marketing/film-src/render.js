const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');const {spawn}=require('child_process');
const [,,a,b,out]=process.argv;const FPS=60;
(async()=>{const br=await chromium.launch();const p=await br.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+__dirname+'/film.html');await p.evaluate(()=>window.ready);
const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','fast','-crf','10','-pix_fmt','yuv420p',out]);
for(let f=+a;f<+b;f++){await p.evaluate(t=>seek(t),f/FPS);const buf=await p.screenshot({type:'jpeg',quality:94});
 if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(f%300===0)console.log(out,f);}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await br.close();console.log('done',out)})();
