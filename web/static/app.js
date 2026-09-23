'use strict';
const $ = id => document.getElementById(id);
const $$ = selector => [...document.querySelectorAll(selector)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = name => '<svg aria-hidden="true"><use href="#i-' + name + '"/></svg>';
const number = (v, digits=1) => typeof v === 'number' && Number.isFinite(v) ? v.toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits}) : '—';
const time = v => {const d = new Date(v); return Number.isNaN(d.valueOf()) ? '时间未知' : d.toLocaleTimeString('zh-CN',{hour12:false});};
const LEVEL = {normal:'正常',watch:'关注',alarm:'告警',critical:'危急'};
const SKILLS = {'engine-room-acoustic-sentinel':'声学异常检测','engine-room-visual-inspector':'视觉巡检','route-deviation-watch':'航线偏离分析','radar-ppi-interpreter':'雷达目标检测','sonar-acoustic-fingerprint':'被动声纹判别','manual-rag-query':'手册检索','navlog-autofill':'值班日志','report-composer':'报告生成','deepstream-generate-pipeline':'DeepStream 管线生成'};
const PAGES = {overview:['值班总览','机舱与航行状态，一眼掌握。'],engine:['机舱监测','声音与仪表。'],situation:['航行态势','雷达、航线与声纹。'],reports:['日志与证据','执行记录与报告。'],manual:['手册检索','带来源的本地检索。'],about:['关于 ShipMind','船端值守智能副驾。']};
const state = {data:{},errors:{},range:8000,target:0,filter:'all',busy:false,page:'overview',lastRefresh:null};
let timer,liveTimer;
function routePage(){
 const name=location.hash.slice(1); state.page=PAGES[name]?name:'overview';
 const [title,subtitle]=PAGES[state.page];
 $('page-title').textContent=title; $('breadcrumb').textContent=title; $('page-subtitle').textContent=subtitle; document.title=title+' · ShipMind 智舷';
 $$('[data-view]').forEach(a=>{if(a.dataset.view===state.page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 $$('[data-pages]').forEach(p=>p.hidden=!p.dataset.pages.split(' ').includes(state.page));
 const isData=!['about','manual'].includes(state.page);
 document.querySelector('.dashboard').hidden=!isData; document.querySelector('.dashboard').dataset.page=state.page;
 document.querySelector('.page-actions').hidden=!isData; document.querySelector('.page-heading').hidden=!isData; $('snapshot-bar').hidden=!isData;
 $('manual-page').hidden=state.page!=='manual'; $('about-page').hidden=state.page!=='about';
 closeMenu(); window.scrollTo(0,0); requestAnimationFrame(drawAll); syncLive();
}
function syncMenu(){const hidden=matchMedia('(max-width:640px)').matches&&!$('sidebar').classList.contains('open');$('sidebar').inert=hidden;}
function closeMenu(){const hadFocus=$('sidebar').contains(document.activeElement);$('sidebar').classList.remove('open');$('menu-toggle').setAttribute('aria-expanded','false');syncMenu();if(hadFocus&&matchMedia('(max-width:640px)').matches)$('menu-toggle').focus({preventScroll:true});}
$('menu-toggle').addEventListener('click',()=>{const open=$('sidebar').classList.toggle('open');$('menu-toggle').setAttribute('aria-expanded',String(open));syncMenu();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
document.addEventListener('click',e=>{if(!e.target.closest('#sidebar')&&!e.target.closest('#menu-toggle'))closeMenu();});
window.addEventListener('hashchange',routePage);
async function api(path){
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),30000);
 try{const r=await fetch(path,{signal:controller.signal,cache:'no-store'});let d;try{d=await r.json();}catch{throw new Error('服务未返回可读取的数据');}
 if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:'请求未完成，请稍后重试');return d;
 }catch(e){if(e.name==='AbortError')throw new Error('等待分析超时，请重试');throw e;}finally{clearTimeout(timeout);}
}
function setError(key,error){
 const box=document.querySelector('[data-error="'+key+'"]');box.hidden=!error; box.closest('.panel').classList.toggle('error',!!error);
 if(error){box.replaceChildren(document.createTextNode((state.data[key]?'上次数据已过期。':'')+error+' '));const b=document.createElement('button');b.textContent='重试';b.addEventListener('click',refresh);box.append(b);}
}
function validate(key,d){
 if(!d||typeof d!=='object')throw new Error('数据格式不完整');
 const ok={alerts:()=>Array.isArray(d.alerts)&&d.alerts.every(x=>LEVEL[x.level]),spectrum:()=>Array.isArray(d.spectrum)&&d.spectrum.length>1&&d.spectrum.every(Number.isFinite)&&Array.isArray(d.freq_labels)&&d.freq_labels.length===d.spectrum.length,visual:()=>typeof d.image_b64==='string'&&!!d.reading,situation:()=>Array.isArray(d.radar?.targets)&&!!LEVEL[d.route?.level]&&typeof d.sonar?.label==='string',trajectory:()=>Array.isArray(d.runs),logs:()=>typeof d.report_md==='string'};
 if(!ok[key]())throw new Error('观测数据不完整，请检查分析服务');
}
const renderers={alerts:renderAlerts,spectrum:renderSpectrum,visual:renderVisual,situation:renderSituation,trajectory:renderTrajectory,logs:renderReport};
async function refresh(){
 if(state.busy)return; state.busy=true; clearTimeout(timer);$('refresh').disabled=true;$('refresh').querySelector('span').textContent='分析中…';
 const results=await Promise.allSettled(Object.keys(renderers).map(async key=>{
  try{const d=await api('/api/'+key);validate(key,d);state.data[key]=d;delete state.errors[key];setError(key,null);renderers[key](d);}
  catch(e){state.errors[key]=e.message;setError(key,e.message);if(key==='logs')$('download-report').disabled=true;throw e;}
 }));
 const failed=results.filter(r=>r.status==='rejected').length;
 state.lastRefresh=new Date();$('updated').textContent=time(state.lastRefresh);$('updated').dateTime=state.lastRefresh.toISOString();
 $('connection').className='connection '+(failed?'bad':'good');$('connection').innerHTML='<span class="dot"></span>'+(failed?failed+' 项观测不可用':'本地服务已连接');
 $('refresh-status').textContent=failed?'刷新完成，'+failed+' 项观测不可用':'六项观测已更新';
 state.busy=false;$('refresh').disabled=false;$('refresh').querySelector('span').textContent='刷新观测';
 timer=setTimeout(()=>{if($('auto-refresh').checked&&!document.hidden&&!['manual','about'].includes(state.page))refresh();else schedule();},30000);
}
function schedule(){clearTimeout(timer);timer=setTimeout(()=>{if($('auto-refresh').checked&&!document.hidden&&!['manual','about'].includes(state.page))refresh();else schedule();},30000);}
$('refresh').addEventListener('click',refresh);
async function liveTick(){
 if(state.busy||document.hidden||['manual','about'].includes(state.page)||!$('auto-refresh').checked)return;
 await Promise.allSettled(['spectrum','visual'].map(async key=>{
  try{const d=await api('/api/'+key);validate(key,d);state.data[key]=d;delete state.errors[key];setError(key,null);renderers[key](d);}
  catch(e){state.errors[key]=e.message;setError(key,e.message);}
 }));
}
function syncLive(){clearInterval(liveTimer);if($('auto-refresh').checked&&!['manual','about'].includes(state.page))liveTimer=setInterval(liveTick,3000);}
$('auto-refresh').addEventListener('change',syncLive);
function renderAlerts(d=state.data.alerts){
 if(!d)return;
 const rows=d.alerts.filter(x=>state.filter==='all'||x.level!=='normal').sort((a,b)=>['critical','alarm','watch','normal'].indexOf(a.level)-['critical','alarm','watch','normal'].indexOf(b.level));
 $('alerts').innerHTML=rows.map(x=>'<article class="alert-item"><div class="alert-head"><strong>'+esc(x.device)+'</strong><span class="badge level-'+esc(x.level)+'">'+esc(LEVEL[x.level])+'</span></div><h3>'+esc(x.level==='normal'?'信号处于基线范围':x.top_feature||'检测到信号变化')+'</h3><p>'+esc(x.level==='normal'?'独立正常样本，作为异常观测的对照。':'可能成因：'+(x.causes||[]).join('、'))+'</p><div class="alert-time"><span>分析 '+esc(time(x.ts))+'</span><b>偏离 '+number(x.delta,3)+'</b></div></article>').join('')||'<p class="empty">当前筛选下没有异常样本。</p>';
}
$$('[data-alert-filter]').forEach(b=>b.addEventListener('click',()=>{state.filter=b.dataset.alertFilter;$$('[data-alert-filter]').forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',String(x===b));});renderAlerts();}));
function canvas(id){
 const c=$(id),w=c.clientWidth,h=c.clientHeight;if(!w||!h)return null;const ratio=Math.min(devicePixelRatio||1,2);
 c.width=Math.round(w*ratio);c.height=Math.round(h*ratio);const ctx=c.getContext('2d');ctx.scale(ratio,ratio);ctx.clearRect(0,0,w,h);return {ctx,w,h};
}
function renderSituation(d){
 const t=d.radar.targets;
 if(state.target>=t.length)state.target=0;
 $('target-count').textContent=String(t.length).padStart(2,'0');
 $('targets').innerHTML=t.map((x,i)=>'<button class="target-button" data-target="'+i+'" aria-pressed="'+(i===state.target)+'"><span><b>目标 '+String(i+1).padStart(2,'0')+'</b><i></i></span><div class="target-measures">'+number(x.bearing_deg)+'° &nbsp; '+number(x.range_m/1000,2)+' km</div></button>').join('')||'<p class="empty">本帧未检出目标</p>';
 $$('[data-target]').forEach(b=>b.addEventListener('click',()=>{state.target=Number(b.dataset.target);$$('[data-target]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));drawRadar();}));
 const labels={large_cargo_or_tanker:'大型货船 / 油轮类',medium_vessel:'中型船舶类',tug_or_fishing:'拖轮 / 渔船类',unknown:'暂无法判别',Cargo:'货船类',Tanker:'油轮类',Tug:'拖轮类',Passengership:'客船类'};
 $('sonar-label').textContent=labels[d.sonar.label]||d.sonar.label;
 $('sonar-confidence').textContent='置信度 '+number(d.sonar.confidence*100,0)+'% · 独立样本，未关联目标';
 $('route-level').textContent=LEVEL[d.route.level];$('route-level').style.color=d.route.level==='normal'?'var(--teal)':'var(--warning)';
 $('route-xte').innerHTML=number(d.route.max_xte_m)+' <small>m</small>';$('route-width').innerHTML=number(d.route.corridor_half_width_m,0)+' <small>m</small>';
 drawRadar();drawRoute();
}
$$('[data-range]').forEach(b=>b.addEventListener('click',()=>{state.range=Number(b.dataset.range);$$('[data-range]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));drawRadar();}));
function drawRadar(){
 const c=canvas('radar');if(!c)return;const {ctx,w,h}=c;
 const cx=w/2,cy=h/2+1,R=Math.min(w/2-32,h/2-33);
 $('radar-range').textContent=number(state.range/1000)+' km';
 if(R<20)return;ctx.lineWidth=1;ctx.strokeStyle='#dbe7f4';
 for(let i=1;i<=4;i++){ctx.beginPath();ctx.arc(cx,cy,R*i/4,0,Math.PI*2);ctx.stroke();}
 for(let deg=0;deg<360;deg+=30){const a=(deg-90)*Math.PI/180;ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+R*Math.cos(a),cy+R*Math.sin(a));ctx.stroke();}
 for(let deg=0;deg<360;deg+=5){const a=(deg-90)*Math.PI/180;ctx.strokeStyle=deg%30===0?'#8aa9c7':'#c8d9ea';ctx.beginPath();ctx.moveTo(cx+(R+3)*Math.cos(a),cy+(R+3)*Math.sin(a));ctx.lineTo(cx+(R+(deg%30===0?9:6))*Math.cos(a),cy+(R+(deg%30===0?9:6))*Math.sin(a));ctx.stroke();}
 ctx.fillStyle='#6e6e73';ctx.font='10px SFMono-Regular, Consolas, monospace';ctx.textAlign='center';ctx.textBaseline='middle';
 ['000°','090°','180°','270°'].forEach((v,i)=>{const a=(i*90-90)*Math.PI/180;ctx.fillText(v,cx+(R+22)*Math.cos(a),cy+(R+18)*Math.sin(a));});
 ctx.font='8px SFMono-Regular, Consolas, monospace';ctx.fillStyle='#8e8e93';for(let i=1;i<4;i++)ctx.fillText(number(state.range*i/4000,0)+' km',cx+5,cy-R*i/4+8);
 const targets=state.data.situation?.radar.targets||[];
 let outside=0;
 targets.forEach((t,i)=>{if(!Number.isFinite(t.bearing_deg)||!Number.isFinite(t.range_m))return;if(t.range_m>state.range){outside++;return;}const a=(t.bearing_deg-90)*Math.PI/180,r=t.range_m/state.range*R,x=cx+r*Math.cos(a),y=cy+r*Math.sin(a);
 ctx.strokeStyle=i===state.target?'#0071e3':'#ff9f0a';ctx.fillStyle='#ff9f0a';ctx.beginPath();ctx.arc(x,y,3.5,0,Math.PI*2);ctx.fill();
 if(i===state.target){ctx.beginPath();ctx.arc(x,y,9,0,Math.PI*2);ctx.stroke();ctx.setLineDash([3,4]);ctx.strokeStyle='#80b9ef';ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(x,y);ctx.stroke();ctx.setLineDash([]);}
 ctx.fillStyle='#1d1d1f';ctx.font='10px SFMono-Regular, Consolas, monospace';ctx.textAlign=x>cx+R*.6?'right':'left';ctx.fillText('T'+String(i+1).padStart(2,'0'),x+(x>cx+R*.6?-14:14),y-8);
 });
 ctx.fillStyle='#0071e3';ctx.beginPath();ctx.moveTo(cx,cy-6);ctx.lineTo(cx+4,cy+5);ctx.lineTo(cx,cy+2);ctx.lineTo(cx-4,cy+5);ctx.closePath();ctx.fill();
 $('out-of-range').textContent=outside?outside+' 个目标超出当前量程':'';
}
function drawRoute(){
 const c=canvas('route-canvas'),r=state.data.situation?.route;if(!c||!r)return;const {ctx,w,h}=c;const pts=[...(r.waypoints||[]),...(r.fixes||[])];if(pts.length<2)return;
 const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),minX=Math.min(...xs),minY=Math.min(...ys),dx=Math.max(...xs)-minX||1,dy=Math.max(...ys)-minY||1;
 const pos=p=>[7+(p[0]-minX)/dx*(w-14),h-8-(p[1]-minY)/dy*(h-16)];
 function line(arr,color,dash){ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.setLineDash(dash);ctx.beginPath();arr.forEach((p,i)=>{const [x,y]=pos(p);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();ctx.setLineDash([]);}
 line(r.waypoints||[],'#8e8e93',[3,3]);line(r.fixes||[],'#0071e3',[]);if(r.fixes?.length){const [x,y]=pos(r.fixes.at(-1));ctx.fillStyle='#0071e3';ctx.beginPath();ctx.arc(x,y,3,0,7);ctx.fill();}
}
function renderSpectrum(d){
 const f=d.features||{};
 $('features').innerHTML=[['均方根',f.rms,3,''],['频谱质心',f.spectral_centroid,0,'Hz'],['波峰因数',f.crest_factor,2,'']].map(([label,v,n,u])=>'<div><span>'+label+'</span><strong>'+number(v,n)+'</strong><small>'+u+'</small></div>').join('');
 drawSpectrum();
}
function drawSpectrum(){
 const c=canvas('spectrum'),d=state.data.spectrum;if(!c||!d)return;const {ctx,w,h}=c;const a=d.spectrum,l=40,r=w-12,t=18,b=h-27,min=Math.floor(Math.min(...a)/10)*10,max=Math.ceil(Math.max(...a)/10)*10+10;
 ctx.font='9px SFMono-Regular, Consolas, monospace';ctx.textAlign='right';ctx.fillStyle='#6e6e73';ctx.strokeStyle='#e5e5ea';
 for(let i=0;i<=3;i++){const y=t+(b-t)*i/3;ctx.fillText(String(Math.round(max-(max-min)*i/3)),l-9,y+3);ctx.beginPath();ctx.moveTo(l,y);ctx.lineTo(r,y);ctx.stroke();}
 ctx.textAlign='left';ctx.fillText('dB',5,10);ctx.fillStyle='#6e6e73';
 for(let i=0;i<=4;i++){const x=l+(r-l)*i/4;ctx.textAlign=i===4?'right':'center';ctx.fillText(number(d.freq_labels.at(-1)*i/4000,1)+'k',x,h-8);}
 ctx.strokeStyle='#0071e3';ctx.lineWidth=1.5;ctx.beginPath();a.forEach((v,i)=>{const x=l+i/(a.length-1)*(r-l),y=b-(v-min)/(max-min)*(b-t);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
 ctx.lineTo(r,b);ctx.lineTo(l,b);ctx.closePath();ctx.fillStyle='rgba(0,113,227,.05)';ctx.fill();
}
function renderVisual(d){
 const rec=d.reading;$('gauge').replaceChildren();const img=document.createElement('img');img.src='data:image/jpeg;base64,'+d.image_b64;img.alt='合成压力表，红色矩形为检测框';$('gauge').append(img);
 const readable=typeof rec.value==='number';$('reading').innerHTML=readable?number(rec.value,2)+'<small>'+esc(rec.unit||'')+'</small>':'待复核';
 $('reading-meta').innerHTML='<dt>置信度</dt><dd>'+number(rec.confidence*100,0)+'%</dd><dt>检测方法</dt><dd>'+esc(({red_needle:'红指针',dark_needle:'黑指针',black_needle:'黑指针'})[rec.method]||rec.method||'未判定')+'</dd>';
}
function renderTrajectory(d){
 const latest=d.latest;if(!latest){$('trajectory-source').textContent='尚无执行记录';$('trajectory').innerHTML='<p class="empty">运行项目的演示流程后，可在这里查看执行步骤。</p>';$('step-count').textContent='0 步';return;}
 const opened=new Set($$('#trajectory details[open]').map(x=>x.dataset.step));
 $('trajectory-source').textContent=latest.path+' · 更新 '+time(latest.updated_at*1000);$('step-count').textContent=latest.steps+' 步';
 $('trajectory').innerHTML=(latest.detail||[]).slice().reverse().map((s,i)=>{const rc=s.returncode;const key=String(latest.steps-i);const fail=rc!==0&&rc!==1;return '<details class="trajectory-step" data-step="'+key+'" '+(opened.has(key)?'open':'')+'><summary><span class="step-dot '+(fail?'fail':'ok')+'"></span><span class="step-name">'+esc(SKILLS[s.skill.replace('official/','')]||s.skill)+'</span><span class="step-duration">'+number(s.duration_s*1000,0)+' ms</span>'+icon('chevron')+'</summary><div class="step-result">'+esc(time(s.ts))+' · 返回码 '+esc(rc)+' · '+(rc===0?'正常退出':rc===1?'告警或审核驳回，详见输出':'执行失败')+'</div><pre>'+esc(JSON.stringify({args:s.args,output:s.output},null,2))+'</pre></details>';}).join('');
}
function markdown(raw){
 // A deliberately small, escaped renderer: raw HTML and remote images are never executed.
 let html='',code=false,lines=[];
 for(const line of raw.split('\n')){
  if(line.startsWith('```')){if(code){html+='<pre>'+esc(lines.join('\n'))+'</pre>';lines=[];}code=!code;continue;}
  if(code){lines.push(line);continue;}
  if(/^#{1,2} /.test(line))html+='<h3>'+esc(line.replace(/^#+ /,''))+'</h3>';
  else if(/^### /.test(line))html+='<h4>'+esc(line.slice(4))+'</h4>';
  else if(line.startsWith('- '))html+='<p>'+esc(line.slice(2).replace('[已核实]','[引用已校验]'))+'</p>';
  else if(line.trim())html+='<p>'+esc(line)+'</p>';
 }
 if(code)html+='<pre>'+esc(lines.join('\n'))+'</pre>';return html;
}
function renderReport(d){
 $('download-report').disabled=!d.report_md;
 $('report').innerHTML=d.report_md?markdown(d.report_md):'<p class="empty">尚无报告。完成态势演示并保存报告后，这里会展示证据汇总。</p>';
 $('report-source').textContent=d.source?'历史报告 · '+d.source+' · '+time(d.source_updated_at*1000):'';
}
$('download-report').addEventListener('click',()=>{const raw=state.data.logs?.report_md;if(!raw||state.errors.logs)return;
 const text='> 范围说明：当前 verifier 仅检查证据引用存在性，不构成专业确认。以下为原始报告。\n\n'+raw;
 const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='ShipMind-值班报告.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
function quoteMarkup(raw){
 const inline=s=>esc(s).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 const lines=String(raw).split('\n');let html='';
 for(let i=0;i<lines.length;i++){
  const line=lines[i].trim();
  if(line.startsWith('|')&&i+1<lines.length&&/^\|[\s:|\-]+\|?$/.test(lines[i+1].trim())){
   const cells=s=>s.trim().replace(/^\|/,'').replace(/\|$/,'').split('|').map(x=>x.trim());
   const headers=cells(line);html+='<div class="quote-table" tabindex="0" role="region" aria-label="手册摘录表格，可横向滚动"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+inline(h)+'</th>').join('')+'</tr></thead><tbody>';i++;
   while(i+1<lines.length&&lines[i+1].trim().startsWith('|')){const row=cells(lines[++i]);html+='<tr>'+headers.map((_,j)=>'<td>'+(row[j]?inline(row[j]):'<span class="muted">摘录未含</span>')+'</td>').join('')+'</tr>';}
   html+='</tbody></table></div>';continue;
  }
  if(line.startsWith('- ')){html+='<ul>';do{html+='<li>'+inline(lines[i].trim().slice(2))+'</li>';if(!lines[i+1]?.trim().startsWith('- '))break;i++;}while(i<lines.length);html+='</ul>';}
  else if(line)html+='<p>'+inline(line)+'</p>';
 }
 return html;
}
let searching=false;
async function searchManual(e){
 e?.preventDefault();const q=$('manual-query').value.trim();if(!q||searching)return;searching=true;$('manual-submit').disabled=true;$('manual-submit').textContent='检索中…';$('manual-results').innerHTML='<p class="empty">正在检索本地手册…</p>';
 try{const d=await api('/api/manual?q='+encodeURIComponent(q));if(!Array.isArray(d.answers))throw new Error('检索返回格式不完整');
 $('manual-results').innerHTML=d.answers.length?'<p class="muted small">找到 '+d.answers.length+' 条相关原文</p>'+d.answers.map(a=>'<article class="manual-result"><header><h3>'+esc(a.section)+'</h3><span class="badge neutral">原文摘录</span></header><blockquote>'+quoteMarkup(a.quote)+'</blockquote><p class="source">来源：'+esc(a.source)+'</p><details class="raw-quote"><summary>查看原始摘录</summary><pre>'+esc(a.quote)+'</pre></details></article>').join(''):'<div class="manual-empty"><h3>没有找到相关原文</h3><p>请尝试更具体的设备名、现象或条款编号。</p></div>';
 }catch(e){$('manual-results').innerHTML='<div class="panel-error" role="alert">'+esc(e.message)+'。请修改关键词或重新检索。</div>';}
 finally{searching=false;$('manual-submit').disabled=false;$('manual-submit').textContent='检索手册';}
}
$('manual-form').addEventListener('submit',searchManual);
$$('[data-query]').forEach(b=>b.addEventListener('click',()=>{$('manual-query').value=b.dataset.query;searchManual();}));
function drawAll(){drawRadar();drawSpectrum();drawRoute();}
let resizeFrame;window.addEventListener('resize',()=>{syncMenu();cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(drawAll);});
function tick(){const d=new Date();$('clock').textContent=d.toLocaleDateString('zh-CN',{month:'2-digit',day:'2-digit'})+' / '+time(d);}
tick();setInterval(tick,1000);routePage();refresh();
