/* Explicit release screenshots; not run by ordinary test suites. */
const {chromium}=require('playwright');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve('web');
const server=http.createServer((req,res)=>{
 const pathname=new URL(req.url,'http://localhost').pathname;
 const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
 if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end()}
 try{res.setHeader('Content-Type',({'.svg':'image/svg+xml','.js':'text/javascript','.css':'text/css','.json':'application/json','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file))}catch{res.writeHead(404);res.end()}
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,...(process.env.NORTHSTAR_BROWSER_CHANNEL?{channel:process.env.NORTHSTAR_BROWSER_CHANNEL}:{})});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const url=`http://127.0.0.1:${server.address().port}`;
 fs.mkdirSync('screenshots',{recursive:true});
 for(const route of ['overview','trust-center','reconciliation','lineage','ai-assistant','incidents']){
  await page.goto(`${url}/#${route}`);await page.waitForSelector('body:not(.is-loading)');await page.waitForSelector('#trust-center .gov-summary',{state:'attached'});
  await page.evaluate(()=>document.fonts.ready);
  let name=route;
  if(route==='lineage')await page.locator('[data-asset="FactSales.COGS"]').click();
  if(route==='ai-assistant'){await page.locator('#ai-question').fill('What was gross margin?');await page.locator('#ai-form button').click();await page.locator('#ai-answer').scrollIntoViewIfNeeded();name='assistant';}
  if(route==='incidents'){await page.locator('#run-incident').click();await page.locator('#incident-summary').scrollIntoViewIfNeeded();name='failure';}
  await page.screenshot({animations:'disabled',path:`screenshots/datrixon-v2-${name}.png`});
 }
 await page.setViewportSize({width:390,height:900});await page.goto(url+'/#trust-center');await page.waitForSelector('#trust-center .gov-summary');await page.screenshot({animations:'disabled',path:'screenshots/datrixon-v2-mobile.png'});
 console.log('Captured six V2 desktop views and mobile Trust Center');
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
