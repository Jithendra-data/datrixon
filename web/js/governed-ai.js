/* Deterministic governed operations. No eval, SQL generation, network provider or raw-table access. */
(function(root,factory){const api=factory();if(typeof module==='object')module.exports=api;else root.DatrixonAI=api})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const dimensions=['schema','quality','referential_integrity','freshness','reconciliation','metric_certification','lineage','access_policy','contract','semantic_equivalence'];
 const scenarios={none:null,reconciliation:'reconciliation',missing_column:'contract',duplicate_invoice:'quality',stale:'freshness',metric_change:'metric_certification',schema_drift:'schema',missing_lineage:'lineage',restricted:'restricted_field',unauthorized:'role_domain_denied'};
 const supported=['What was revenue in 2025?','What was gross margin?','Which customers became inactive?','Which products have the highest inventory exposure?','Which vendors have overdue purchase orders?','Why did gross margin change?','Show revenue by month.','What controls validate revenue?','Where does Gross Margin come from?','Can AI safely use the inventory metric?'];
 function decision(g,id,now=new Date(),scenario='none'){
   const original=g?.decisions?.[id];const controls={};
   for(const key of dimensions)controls[key]=original?.controls?.[key]||'FAIL';
   const age=(now-new Date(g?.version_identity?.timestamp))/3600000;
   if(!Number.isFinite(age)||age<0||age>(g?.freshness?.max_age_hours??192))controls.freshness='FAIL';
   if(scenarios[scenario]&&dimensions.includes(scenarios[scenario]))controls[scenarios[scenario]]='FAIL';
   const failed=dimensions.filter(k=>!['PASS','WARNING'].includes(controls[k]));
   return {asset:id,status:failed.length?'BLOCKED':Object.values(controls).includes('WARNING')?'WARNING':'TRUSTED',controls,failed_controls:failed};
 }
 function policy(g,metric,trust,role,operation='ai',scenario='none'){
   const reasons=[];
   if(!['ai','view','publish'].includes(operation))reasons.push('unknown_operation');
   if(!Object.hasOwn(g.policy.roles,role)||!Array.isArray(g.policy.roles[role])||!g.policy.roles[role].includes(metric.domain))reasons.push('role_domain_denied');
   if(!metric.permitted_roles.includes(role))reasons.push('metric_role_denied');
   if(metric.sensitivity==='Restricted'||scenario==='restricted')reasons.push('restricted_field');
   if(metric.certification_status!=='CERTIFIED_DEMO')reasons.push('uncertified_metric');
   if(!['TRUSTED','WARNING'].includes(trust.status))reasons.push(...(trust.failed_controls.length?trust.failed_controls:['missing_trust']));
   if(scenario==='unauthorized')reasons.push('role_domain_denied');
   return {decision:reasons.length?'DENY':'ALLOW',reasons:[...new Set(reasons)],metric:metric.metric_id,role,operation,boundary:'Demo role simulation — not production authentication'};
 }
 function parse(question){
   if(typeof question!=='string'||question.length>500)return null;
   const q=question.toLowerCase().trim().replace(/[?.]+$/,'').replace(/\s+/g,' ');
   if(/\b(address(?:es)?|password|secret|token|credit limit|restricted)\b/.test(q))return {op:'restricted',ids:[]};
   const scalar=q.match(/^(?:what (?:was|is)|show(?: me)?) (?:the )?(revenue|gross margin|gross profit|net sales|average order value|return rate|inventory balance|inventory exposure|inventory velocity|vendor fill rate|order volume|outstanding purchasing exposure)(?: in (20\d{2}))?$/);
   const names={'revenue':'revenue','gross margin':'gross_margin','gross profit':'gross_profit','net sales':'net_sales','average order value':'average_order_value','return rate':'return_rate','inventory balance':'inventory_value','inventory exposure':'inventory_exposure','inventory velocity':'inventory_velocity','vendor fill rate':'vendor_fill_rate','order volume':'orders','outstanding purchasing exposure':'open_po_value'};
   if(scalar)return {op:'scalar',ids:[names[scalar[1]]],year:scalar[2]||null};
   if(q==='which customers became inactive')return {op:'customers',ids:['inactive_customers']};
   if(q==='which products have the highest inventory exposure')return {op:'inventory',ids:['inventory_exposure']};
   if(q==='which vendors have overdue purchase orders')return {op:'purchasing',ids:['overdue_po_value','overdue_purchase_orders']};
   if(q==='why did gross margin change')return {op:'margin_change',ids:['gross_margin','revenue','gross_profit']};
   if(q==='show revenue by month')return {op:'monthly',ids:['revenue']};
   if(q==='what controls validate revenue')return {op:'controls',ids:['revenue']};
   if(q==='where does gross margin come from')return {op:'lineage',ids:['gross_margin']};
   if(q==='can ai safely use the inventory metric')return {op:'readiness',ids:['inventory_value']};
   return null;
 }
 const format=(v,unit)=>v==null?'Undefined (zero denominator or no observations)':unit==='ratio'?(v*100).toFixed(2)+'%':new Intl.NumberFormat('en-US',{maximumFractionDigits:2,...(unit==='USD'?{style:'currency',currency:'USD'}:{})}).format(v)+(unit==='USD'?'':' '+unit);
 function impact(edges,asset){const found=new Set(),queue=[asset];while(queue.length){const current=queue.shift();for(const edge of edges)if(edge.upstream_asset===current&&!found.has(edge.downstream_asset)){found.add(edge.downstream_asset);queue.push(edge.downstream_asset)}}return [...found].sort()}
 function answer(data,question,role='Executive',scenario='none',now=new Date()){
   const g=data.governance,operation=parse(question);
   const result={answer_id:typeof crypto!=='undefined'&&crypto.randomUUID?crypto.randomUUID():'answer-'+now.getTime()+'-'+Math.random().toString(36).slice(2),question:String(question).slice(0,500),timestamp:now.toISOString(),business_cutoff:g?.version_identity?.business_cutoff,
     data_version:g?.version_identity?.dataset_version,latest_approved_run:g?.version_identity?.run_id,metric_ids:operation?.ids||[],source_assets:[],evidence:[],status:'BLOCKED',text:'Unsupported question. Choose a supported question; no data was queried.',rows:[],policy_decision:'DENY',simulation:scenario!=='none',logic:operation?.op||'unsupported'};
   if(!g||!operation)return result;
   if(data.pipeline_metadata?.publication_status!=='APPROVED'){result.text='Dataset has no publication approval. No analytical result is available.';return result}
   if(operation.op==='restricted'){result.text='Access denied: Restricted fields are outside the governed analytical interface.';result.policy_reason='restricted_field';result.trust_status='BLOCKED';return result}
   for(const id of operation.ids){
     const metric=g.registry.metrics.find(m=>m.metric_id===id);
     if(!metric){result.text='Metric definition is unavailable.';return result}
     const trust=decision(g,id,now,scenario);
     const required=metric.reconciliation_rule.map(name=>data.reconciliation.find(r=>r.Measure===name));
     if(required.some(r=>!r||r.Status!=='PASS'||Math.max(Math.abs(r.RawValue-r.FactValue),Math.abs(r.RawValue-r.DashboardValue))>r.Tolerance)){
       trust.controls.reconciliation='FAIL';trust.status='BLOCKED';trust.failed_controls.push('reconciliation');
     }
     const authorization=policy(g,metric,trust,role,'ai',scenario);
     result.evidence.push({metric_id:id,version:metric.version,definition:metric.business_definition,source_assets:g.values[id]?.dependencies||metric.source_columns,
       query:g.values[id]?.query||metric.calculation,trust,policy:authorization,reconciliation:data.reconciliation.filter(r=>metric.reconciliation_rule.includes(r.Measure)).map(r=>authorization.decision==='ALLOW'?r:{Measure:r.Measure,Status:r.Status,details:'Totals withheld by the policy/trust gate'}),
       lineage_reference:'#lineage',metric_reference:'#metric-catalog',controls_reference:'#quality',business_cutoff:result.business_cutoff,data_version:result.data_version});
   }
   result.source_assets=[...new Set(result.evidence.flatMap(e=>e.source_assets))];
   result.trust_status=result.evidence.some(e=>e.trust.status==='BLOCKED')?'BLOCKED':result.evidence.some(e=>e.trust.status==='WARNING')?'WARNING':'TRUSTED';
   result.reconciliation_status=result.evidence.flatMap(e=>e.reconciliation).some(r=>r.Status!=='PASS')?'FAIL':'See applicable evidence';
   const denied=result.evidence.filter(e=>e.policy.decision==='DENY');
   if(denied.length){result.text='Answer unavailable: '+[...new Set(denied.flatMap(e=>e.policy.reasons))].join(', ')+'. The latest approved dataset remains unchanged. Inspect controls, correct the issue, and rerun the pipeline.';return result}
   if(operation.year&&(!g.periods[operation.year]||!Object.hasOwn(g.periods[operation.year],operation.ids[0]))){result.text='That period is unavailable for this metric. No value was inferred.';return result}
   result.status='ANSWERED';result.policy_decision='ALLOW';
   const metric=g.registry.metrics.find(m=>m.metric_id===operation.ids[0]);
   if(operation.op==='scalar')result.text=`${metric.display_name}${operation.year?' in '+operation.year:' across the approved dataset'}: ${format(operation.year?g.periods[operation.year][metric.metric_id]:g.values[metric.metric_id].value,metric.unit)}.`;
   else if(['customers','inventory','purchasing'].includes(operation.op)){
     const extract=data.investigations[operation.op];result.rows=extract.rows.slice(0,10);
     result.text=`${extract.total} eligible records. Showing ${result.rows.length} of ${extract.exported} published investigation rows. ${extract.rule}. This is an investigation extract, not an exhaustive answer or a new inactivity transition.`;
   }else if(operation.op==='monthly'){result.rows=data.sales_trend.map(r=>({Month:r.YearMonth,Revenue:r.Revenue}));result.text='Approved monthly invoiced revenue, all regions. Same reporting series used by the dashboard.'}
   else if(operation.op==='margin_change'){
     const years=Object.keys(g.periods).sort(),a=g.periods[years.at(-2)],b=g.periods[years.at(-1)];
     if(!a||a.gross_margin==null||b.gross_margin==null){result.status='BLOCKED';result.policy_decision='DENY';result.text='Insufficient comparable annual evidence.'}
     else result.text=`Gross margin changed by ${((b.gross_margin-a.gross_margin)*100).toFixed(2)} percentage points from ${years.at(-2)} to ${years.at(-1)}. Revenue: ${format(a.revenue,'USD')} → ${format(b.revenue,'USD')}; gross profit: ${format(a.gross_profit,'USD')} → ${format(b.gross_profit,'USD')}. This is an arithmetic comparison, not proof of causality. Check period coverage and category mix before attributing causes.`;
   }else if(operation.op==='controls'){result.rows=g.controls.filter(c=>c.category!=='contract').map(c=>({Control:c.name,Status:c.status,Evidence:c.evidence_reference}));result.text='Revenue uses source eligibility, arithmetic, key controls, semantic equivalence and independent reconciliation. Global source checks protect the entire publication.'}
   else if(operation.op==='lineage'){result.rows=g.lineage.filter(e=>e.metric==='gross_margin');result.text=metric.business_definition+' The following dependencies were traced from executed SQL reads and reviewed loader mappings.'}
   else if(operation.op==='readiness')result.text='Inventory AI readiness: '+(result.trust_status==='WARNING'?'Conditional. The acknowledged synthetic negative-ledger exception remains visible.':'Ready for this synthetic demonstration.')+' This is a deterministic governance assessment, not an AI confidence score.';
   return result;
 }
 class LocalAnalyticalProvider{answer(...args){return answer(...args)}}
 // A future provider may propose only a supported question/operation; its proposal must still pass answer().
 return {answer,parse,decision,policy,impact,format,supported,scenarios,LocalAnalyticalProvider};
});
