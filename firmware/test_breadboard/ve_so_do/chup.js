const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1420,height:900},deviceScaleFactor:2});
const e=[];p.on('pageerror',x=>e.push(x.message));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(400);
await p.screenshot({path:process.argv[3],fullPage:true});console.log(e);await b.close();})();
