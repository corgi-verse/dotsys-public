'use strict';
const field=document.querySelector('#field');
const dog=document.querySelector('#dog');
const shape=document.querySelector('#dog-shape');
const ball=document.querySelector('#ball');
const throwButton=document.querySelector('#throw');
const status=document.querySelector('#status');
const score=document.querySelector('#score');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
let frame=0,busy=false,returns=0;
const HOME=105;
function position(x,facing=1){dog.setAttribute('transform',`translate(${x} 270)`);shape.setAttribute('transform',`scale(${facing} 1)`);}
function ballAt(x,y){ball.setAttribute('cx',x);ball.setAttribute('cy',y);}
function reset(){cancelAnimationFrame(frame);frame=0;busy=false;returns=0;position(HOME);ballAt(178,291);throwButton.setAttribute('aria-disabled','false');throwButton.textContent='Throw the ball';score.textContent='0 happy returns';status.textContent='Ready when you are.';field.dataset.state='ready';}
function play(target=590){
 if(busy)return;
 busy=true;throwButton.setAttribute('aria-disabled','true');field.dataset.state='throwing';status.textContent='Ball away!';
 const destination=Math.max(280,Math.min(710,target));const start=performance.now();const speed=reduced.matches?0.025:1;let phase='';
 function tick(now){
  const elapsed=(now-start)/speed;
  if(elapsed<450){const t=elapsed/450;ballAt(178+(destination-178)*t,291-130*Math.sin(t*Math.PI));}
  else if(elapsed<1300){
   if(phase!=='out'){phase='out';status.textContent='Fetching…';field.dataset.state='fetching';}
   const t=(elapsed-450)/850;position(HOME+(destination-54-HOME)*t);ballAt(destination,291);
  }else if(elapsed<2150){
   if(phase!=='back'){phase='back';status.textContent='Coming back with your ball…';field.dataset.state='returning';}
   const t=(elapsed-1300)/850;const x=destination-54+(HOME-(destination-54))*t;position(x,-1);ballAt(x-62,275);
  }else{
   position(HOME);ballAt(178,291);returns++;busy=false;frame=0;field.dataset.state='ready';throwButton.setAttribute('aria-disabled','false');throwButton.textContent='Play again';score.textContent=`${returns} happy return${returns===1?'':'s'}`;status.textContent='Back with your ball. Play again!';return;
  }
  frame=requestAnimationFrame(tick);
 }
 frame=requestAnimationFrame(tick);
}
throwButton.addEventListener('click',()=>play());
document.querySelector('#garden').addEventListener('click',event=>{const bounds=field.getBoundingClientRect();play((event.clientX-bounds.left)/bounds.width*800);});
document.querySelector('#reset').addEventListener('click',reset);
document.addEventListener('keydown',event=>{if(event.key==='Escape')reset();});
reset();
