'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const code=fs.readFileSync(path.join(__dirname,'../tools/project-radar/radar.js'),'utf8');
function radar(){
 const nodes=new Map();
 function element(){return {textContent:'',children:[],replaceChildren(){this.children=[];},append(child){this.children.push(child);},addEventListener(){},set innerHTML(value){assert.fail('Untrusted HTML rendering');}};}
 const context=vm.createContext({document:{getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);},createElement:element},structuredClone,URL});
 vm.runInContext(code,context);
 return {nodes,initial:JSON.parse(vm.runInContext('JSON.stringify(SAMPLE)',context)),show(value){context.input=value;vm.runInContext('display(input,"test selection")',context);return nodes.get('delta').textContent;}};
}
test('deletion is visible in both lists and does not imply completion',()=>{
 const page=radar();const next=structuredClone(page.initial);next.completed.shift();next.unresolved.shift();
 const delta=page.show(next);
 assert.match(delta,/completed items — 0 added, 0 changed, 1 removed/);
 assert.match(delta,/unresolved items — 0 added, 0 changed, 1 removed/);
 assert.match(delta,/Removal alone does not establish resolution or completion/);
 assert.doesNotMatch(delta,/moved from unresolved to completed/);
});
test('unresolved to completed is an explicit unverified source claim',()=>{
 const page=radar();const next=structuredClone(page.initial);const row=next.unresolved.shift();next.completed.push({...row,text:'The selected source reports this done.',evidence:'Source supplied evidence, not independent verification.'});
 const delta=page.show(next);
 assert.match(delta,/completed items — 1 added, 0 changed, 0 removed/);
 assert.match(delta,/unresolved items — 0 added, 0 changed, 1 removed/);
 assert.match(delta,/1 item\(s\) moved from unresolved to completed/);
 assert.match(delta,/not independently verified here/);
 assert.match(delta,/Removal alone does not establish/);
});
test('edits to text or evidence count by ID without being additions',()=>{
 const page=radar();const next=structuredClone(page.initial);next.completed[0].text='Edited completion statement';next.unresolved[0].evidence='Changed evidence';
 const delta=page.show(next);
 assert.match(delta,/completed items — 0 added, 1 changed, 0 removed/);
 assert.match(delta,/unresolved items — 0 added, 1 changed, 0 removed/);
});
test('new IDs count as additions in each list',()=>{
 const page=radar();const next=structuredClone(page.initial);
 for(const key of ['completed','unresolved'])next[key].push({id:'new-'+key,text:'A new row',evidence:'An explicit test fixture'});
 const delta=page.show(next);
 for(const key of ['completed','unresolved'])assert.match(delta,new RegExp(key+' items — 1 added, 0 changed, 0 removed'));
});
test('unchanged, reordered rows and reordered JSON fields are unchanged',()=>{
 const page=radar();const next=structuredClone(page.initial);
 for(const key of ['completed','unresolved'])next[key]=next[key].reverse().map(row=>({evidence:row.evidence,text:row.text,id:row.id}));
 const delta=page.show(next);
 for(const key of ['completed','unresolved'])assert.match(delta,new RegExp(key+' items — 0 added, 0 changed, 0 removed'));
 assert.doesNotMatch(delta,/Removal alone|moved from unresolved/);
});
test('comparison follows the last valid selection and invalid data preserves it',()=>{
 const page=radar();const next=structuredClone(page.initial);next.unresolved.pop();page.show(next);
 const previous=page.nodes.get('delta').textContent;
 assert.throws(()=>page.show({...next,extra:true}),/Unsupported snapshot/);
 assert.equal(page.nodes.get('delta').textContent,previous);
 assert.match(page.show(next),/unresolved items — 0 added, 0 changed, 0 removed/);
});
test('different projects are not compared and user text stays inert',()=>{
 const page=radar();const next=structuredClone(page.initial);next.source.project='Other project';next.completed[0].text='<img src=x onerror=alert(1)>';
 assert.match(page.show(next),/Selected a different project/);
 assert.equal(page.nodes.get('completed').children[0].textContent,'<img src=x onerror=alert(1)>');
});
