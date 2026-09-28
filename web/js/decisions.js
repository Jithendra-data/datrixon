/* Summaries describe evidence; they do not make autonomous recommendations. */
function performanceSummary(period){
 const change=(value,unit)=>value===null?'not comparable':`${value>=0?'increased':'decreased'} ${Math.abs(value).toFixed(1)} ${unit}`;
 return `Revenue ${change(period.changes.Revenue,'percent')}; gross profit ${change(period.changes.GrossProfit,'percent')}; gross margin ${change(period.changes.margin,'percentage points')} versus the same selected months last year. Investigate the drivers before making pricing decisions.`;
}
function renderPerformanceSummary(period){
 let box=document.querySelector('#performance-summary');
 if(!box){box=document.createElement('section');box.id='performance-summary';box.className='decision-summary';document.querySelector('.kpi-grid').after(box)}
 box.innerHTML=`<h2>Performance Summary</h2><p>${h(performanceSummary(period))}</p><small>Selected financial period and region. Operational signals below use their separately stated scope.</small>`;
}
function renderDomainSummaries(data){
 const e=data.decision_evidence,f=data.business_findings,k=data.executive_kpis;if(!e)return;
 const n=v=>new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(v);
 const pct=(a,b)=>b?`${(a/b*100).toFixed(1)}%`:'Unavailable';
 const texts={
 sales:`Across all available history, ${e.sales.strongest_category.CategoryName} has the highest category margin (${pct(e.sales.strongest_category.GrossProfit,e.sales.strongest_category.Revenue)}); ${e.sales.weakest_category.CategoryName} has the lowest (${pct(e.sales.weakest_category.GrossProfit,e.sales.weakest_category.Revenue)}). Compare category mix and discount evidence before changing prices. Selected-period movement is available on Executive Overview.`,
 customers:`${n(f.valuable_customers_inactive_over_60_days)} accounts meet the valuable-inactive rule. The top 10 customers contribute ${pct(f.customer_top10_revenue_share,1)} of historical invoiced revenue. ${n(e.customers.declining_accounts)} of ${n(e.customers.prior_active_accounts)} prior-active accounts declined in ${e.customers.comparison_year} versus ${e.customers.prior_year}; these calendar-year counts use the full source population.`,
 inventory:`Of ${n(e.inventory.positions)} SKU/warehouse positions: ${n(e.inventory.negative_positions)} have negative ledger balances; ${n(e.inventory.no_shipments_positions)} hold positive stock with no shipments in 90 days; ${n(e.inventory.excess_positions)} exceed 90 days of coverage; ${n(e.inventory.low_coverage_positions)} have nonnegative stock and under 14 days of coverage. Review ledger exceptions separately from replenishment and disposition candidates.`,
 purchasing:`${money(k.open_po_value)} remains unreceived, including ${money(f.overdue_po_value)} overdue. Received ${n(e.purchasing.received_units)} of ${n(e.purchasing.ordered_units)} ordered units (${pct(e.purchasing.received_units,e.purchasing.ordered_units)} quantity fill). Lead times describe ${n(e.purchasing.receipt_events)} receipt events, not delivery OTIF.`,
 operations:`${n(e.operations.on_time_orders)} of ${n(e.operations.shipped_orders)} shipped orders met their requested ship date (${pct(e.operations.on_time_orders,e.operations.shipped_orders)}). Order-to-ship time: mean ${n(e.operations.mean_days)}, median ${n(e.operations.median_days)}, p90 ${n(e.operations.p90_days)} days. Compare warehouses and return reasons to choose an investigation.`};
 for(const [id,text] of Object.entries(texts))document.querySelector(`#${id}>p`).insertAdjacentHTML('afterend',`<aside class="decision-summary"><h3>Decision context</h3><p>${h(text)}</p></aside>`);
}
if(typeof module!=='undefined')module.exports={performanceSummary};
