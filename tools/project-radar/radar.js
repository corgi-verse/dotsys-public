'use strict';
const SAMPLE={"schema":"dotsys.radar/1","source":{"project":"DotSys","revision":"ea31742a189b1e66609919381a6cdb3e45ba141b","as_of":"2026-10-23T05:02:55Z","url":"https://github.com/corgi-verse/dotsys-public/tree/ea31742a189b1e66609919381a6cdb3e45ba141b"},"completed":[{"id":"flagship","text":"Visual Concept Kit 1.1 preserves real listening-room images, editable briefs and a controlled clay-chair direction.","evidence":"Source includes the actual original/edit prompts and image hashes. Prior 1.0 browser receipts are historical; 1.1 accessible descriptions and PNG dimensions are tested offline."},{"id":"integrity","text":"Package-wide contribution review integrity is corrected on public main.","evidence":"PR #2 merged at this revision after independent closure. Manifest, image/brief/CSS, process/evidence, license/notices, tool source and exact submission are bound to review. Local tests: 78 Python, 11 Paste Inbox, 2 Node; no GitHub CI is configured."}],"unresolved":[{"id":"domain","text":"Custom-domain acceptance remains unresolved.","evidence":"Recorded owner verification found new toolbox content at dotsys.vercel.app, old content at dotsys.dev, and a www DNS failure. Actual DNS/Worker/Pages configuration remains uninspected."},{"id":"website-release","text":"Fresh 1.1 browser qualification, the small collection and revised website release remain separate work.","evidence":"This snapshot is pinned to the public integrity correction. It does not claim a later website publication, current live feed or independent community adoption."}],"versions":{"expected":"Give your dot a bigger toolbox \u2014 Vercel website source a492a2c at the recorded verification","observed":"dotsys.dev: Ideas become projects. Projects become a System; www DNS failure at the recorded verification","explanation":"The observed custom domain and current Vercel deployment served different content. Routing/DNS/edge configuration has not been fully inspected, so the exact cause is unresolved. A main commit or Ready deployment does not establish custom-domain acceptance."},"next":["Finish current-version browser and collection acceptance, preserving exact artifacts and source receipts.","Publish the revised website after qualified release review and owner authorization. Local verification is not production acceptance.","Site maintainer: inspect actual authoritative DNS/routing/Worker/Pages configuration with authorized access before any change.","Select a newer reviewed source snapshot when evidence changes. This tool does not fetch updates or connect to Records/cross-chat feeds."]};
const $=id=>document.getElementById(id);let selected=null;let loadSequence=0;
function exact(value,keys){return value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join('|')===[...keys].sort().join('|');}
function bounded(value){return typeof value==='string'&&value.trim().length>0&&value.length<=4000;}
function validate(value){
 if(!exact(value,['schema','source','completed','unresolved','versions','next'])||value.schema!=='dotsys.radar/1')throw Error('Unsupported snapshot schema or fields.');
 if(!exact(value.source,['project','revision','as_of','url'])||!Object.values(value.source).every(bounded))throw Error('Incomplete source identity.');
 const url=new URL(value.source.url);if(url.protocol!=='https:'||url.username||url.password)throw Error('Source must be an HTTPS URL without credentials.');
 if(!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(value.source.as_of)||Number.isNaN(Date.parse(value.source.as_of))||new Date(value.source.as_of).toISOString().replace('.000Z','Z')!==value.source.as_of)throw Error('Use a valid UTC snapshot timestamp.');
 for(const key of ['completed','unresolved']){
  if(!Array.isArray(value[key])||value[key].length>100)throw Error('Expected bounded evidence lists.');
  const ids=new Set();for(const row of value[key]){if(!exact(row,['id','text','evidence'])||!Object.values(row).every(bounded)||ids.has(row.id))throw Error('Evidence rows need unique ids, text and evidence.');ids.add(row.id);}
 }
 if(!exact(value.versions,['expected','observed','explanation'])||!Object.values(value.versions).every(bounded))throw Error('Version evidence is incomplete.');
 if(!Array.isArray(value.next)||!value.next.length||value.next.length>30||!value.next.every(bounded))throw Error('Next actions are required.');
 return value;
}
function list(id,items){const target=$(id);target.replaceChildren();for(const row of items){const li=document.createElement('li');li.textContent=typeof row==='string'?row:row.text;if(typeof row!=='string'){const small=document.createElement('small');small.textContent=row.evidence;li.append(small);}target.append(li);}if(!items.length){const li=document.createElement('li');li.textContent='None recorded in this snapshot.';target.append(li);}}
function display(value,label){
 validate(value);const previous=selected;selected=structuredClone(value);
 $('report-title').textContent=value.source.project;
 $('headline').textContent='What changed in '+value.source.project+'?';
 $('revision').textContent='SELECTED REVISION / '+value.source.revision;
 $('as-of').textContent='Evidence as of '+value.source.as_of+' · '+label;
 $('source-link').href=value.source.url;
 for(const key of ['completed','unresolved','next'])list(key,value[key]);
 for(const key of ['expected','observed','explanation'])$(key).textContent=value.versions[key];
 let delta='First selection. This report reflects the chosen snapshot only.';
 if(previous&&previous.source.project===value.source.project){const changed=key=>value[key].filter(row=>!previous[key].some(old=>JSON.stringify(old)===JSON.stringify(row))).length;delta=`Updated selection: ${changed('completed')} new or changed completed item(s); ${changed('unresolved')} new or changed unresolved item(s). Previous revision: ${previous.source.revision}.`;}
 else if(previous)delta='Selected a different project. This report now follows '+value.source.project+'.';
 $('delta').textContent=delta;$('load-status').className='';$('load-status').textContent='Loaded '+value.source.project+' from '+label+'.';
}
$('snapshot').addEventListener('change',async event=>{const sequence=++loadSequence;const file=event.target.files[0];if(!file)return;try{if(file.size>256_000)throw Error('Snapshot exceeds 256 KB.');const value=JSON.parse(await file.text());if(sequence===loadSequence)display(value,'selected file '+file.name);}catch(error){if(sequence===loadSequence){$('load-status').className='error';$('load-status').textContent='Could not load snapshot: '+error.message+' The last valid report is preserved.';}}});
$('sample').addEventListener('click',()=>{loadSequence++;$('snapshot').value='';display(SAMPLE,'bundled dated snapshot');});
$('download').addEventListener('click',()=>{let url;try{url=URL.createObjectURL(new Blob([JSON.stringify(selected,null,2)+'\n'],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='selected-project-snapshot.json';link.click();$('load-status').textContent='Download requested. Reopen that JSON through the source picker to restore this report.';}catch(error){$('load-status').textContent='Download unavailable. The report is preserved; keep the original selected source file.';}finally{if(url)setTimeout(()=>URL.revokeObjectURL(url),1000);}});
display(SAMPLE,'bundled dated snapshot');
