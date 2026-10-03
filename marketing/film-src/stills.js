// Render stills: node stills.js 3.5 12 ...  → build/stills/s_<t>.jpg
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
 const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('file://'+__dirname+'/film.html');await p.evaluate(()=>window.ready);
 require('fs').mkdirSync(__dirname+'/build/stills',{recursive:true});
 for(const t of process.argv.slice(2).map(Number)){await p.evaluate(t=>seek(t),t);await p.screenshot({path:`${__dirname}/build/stills/s_${t.toFixed(2)}.jpg`,type:'jpeg',quality:80})}
 console.log('errors:',errs.slice(0,5));await b.close()})();
