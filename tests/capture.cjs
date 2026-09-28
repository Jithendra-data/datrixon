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
 const browser=await chromium.launch({headless:true,channel:process.env.NORTHSTAR_BROWSER_CHANNEL||'msedge'});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const url=`http://127.0.0.1:${server.address().port}`;
 fs.mkdirSync('screenshots',{recursive:true});
 for(const route of ['overview','sales','quality','architecture','inventory']){
  await page.goto(`${url}/#${route}`);await page.waitForSelector('body:not(.is-loading)');
  await page.evaluate(()=>document.fonts.ready);if(route==='overview')await page.evaluate(()=>window.scrollTo(0,0));
  if(route==='inventory')await page.locator('#investigation-inventory summary').click();
  if(route==='architecture')await page.locator('[data-stage="3"]').click();
  await page.screenshot({animations:'disabled',path:`screenshots/datrixon-${route}.png`});
 }
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.waitForSelector('body:not(.is-loading)');await page.screenshot({animations:'disabled',path:'screenshots/datrixon-mobile.png'});
 await page.setViewportSize({width:1200,height:630});await page.goto(url+'/assets/preview.svg');await page.screenshot({animations:'disabled',path:'web/assets/preview.png'});
 console.log('Captured six Datrixon views and stable social preview');
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
