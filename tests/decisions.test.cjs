const {test}=require('node:test');
const assert=require('node:assert/strict');
const {performanceSummary}=require('../web/js/decisions.js');
test('summary uses supplied changes and correct units',()=>{
 const text=performanceSummary({changes:{Revenue:12.3,GrossProfit:-2.1,margin:-.4}});
 assert.match(text,/Revenue increased 12.3 percent/);
 assert.match(text,/gross profit decreased 2.1 percent/);
 assert.match(text,/gross margin decreased 0.4 percentage points/);
});
test('unavailable comparisons are not invented',()=>{
 assert.match(performanceSummary({changes:{Revenue:null,GrossProfit:null,margin:null}}),/not comparable/);
});
