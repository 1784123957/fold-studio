<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Box, Layers3, Download, Save, RotateCcw, ArrowUpRight, Plus, Trash2, Move3d, Check, CircleHelp } from 'lucide-vue-next'
import BoxScene from './components/BoxScene.vue'
import NetView from './components/NetView.vue'
import type { BoxDimensions, Geometry, Design, Pad } from './types'
const api = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const input=ref<BoxDimensions>({length:240,width:160,height:100,thickness:0})
const geometry=ref<Geometry>(),designs=ref<Design[]>([]),online=ref(false),busy=ref(false),message=ref(''),failed=ref(false)
const unfold=ref(0),tab=ref('3d'),scene=ref<InstanceType<typeof BoxScene>>(),name=ref('未命名长方体'),saving=ref(false)
const pads=ref<Pad[]>([]), selectedPadId=ref('')
const selectedPad=computed(()=>pads.value.find(p=>p.id===selectedPadId.value))
function isValidPad(p:Pad){return [p.length,p.width,p.height].every(v=>Number.isFinite(v)&&v>=1&&v<=10000)&&[p.x,p.y,p.z].every(v=>Number.isFinite(v)&&Math.abs(v)<=100000)}
const padsValid=computed(()=>pads.value.every(p=>p.name.trim()&&isValidPad(p)))
const visiblePads=computed(()=>pads.value.filter(isValidPad))
function addPad(){if(pads.value.length>=100)return;const p:Pad={id:crypto.randomUUID(),name:`垫块 ${pads.value.length+1}`,length:40,width:30,height:15,x:0,y:dimensions.value.thickness,z:0};pads.value.push(p);selectedPadId.value=p.id;tab.value='3d'}
function deletePad(){pads.value=pads.value.filter(p=>p.id!==selectedPadId.value);selectedPadId.value=pads.value[0]?.id||''}
const dimensions=computed(()=>geometry.value?{length:geometry.value.length,width:geometry.value.width,height:geometry.value.height,thickness:geometry.value.thickness}:input.value)
const valid=computed(()=>[input.value.length,input.value.width,input.value.height].every(v=>Number.isFinite(v)&&v>=1&&v<=10000)&&Number.isFinite(input.value.thickness)&&input.value.thickness>=0&&input.value.thickness<=1000&&2*input.value.thickness<Math.min(input.value.length,input.value.width,input.value.height))
const changed=computed(()=>!geometry.value||(['length','width','height','thickness'] as const).some(k=>input.value[k]!==geometry.value![k]))
const netPad=computed(()=>geometry.value?Math.max(geometry.value.net_width,geometry.value.net_height)*.12:0)
const font=computed(()=>geometry.value?Math.max(geometry.value.net_width,geometry.value.net_height)*.022:12)
let noticeTimer:ReturnType<typeof setTimeout>, animation=0
function notify(text:string,error=false){message.value=text;failed.value=error;clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>message.value='',5000)}
async function request(path:string,options:RequestInit={}) {const r=await fetch(api+path,{...options,signal:AbortSignal.timeout(10000),headers:{'Content-Type':'application/json',...options.headers}});if(!r.ok)throw new Error(`请求失败 (${r.status})`);return r}
async function generate(){if(!valid.value){notify('请输入 1–10000 mm 之间的有效尺寸',true);return}busy.value=true;try{geometry.value=await(await request('/api/geometry',{method:'POST',body:JSON.stringify(input.value)})).json()}catch{notify('生成失败，请检查后端服务是否启动',true)}finally{busy.value=false}}
async function refresh(){try{designs.value=await(await request('/api/designs')).json()}catch{notify('读取方案失败',true)}}
async function save(){if(!geometry.value||!padsValid.value)return;if(!name.value.trim()){notify('请填写方案名称',true);return}saving.value=true;try{await request('/api/designs',{method:'POST',body:JSON.stringify({...dimensions.value,pads:pads.value,name:name.value.trim()})});await refresh();notify('方案已保存到 MySQL')}catch{notify('保存失败，请检查数据库连接',true)}finally{saving.value=false}}
async function remove(id:number){try{await request(`/api/designs/${id}`,{method:'DELETE'});await refresh();notify('方案已删除')}catch{notify('删除失败',true)}}
async function load(d:Design){input.value={length:d.length,width:d.width,height:d.height,thickness:d.thickness??0};name.value=d.name;pads.value=JSON.parse(JSON.stringify(d.pads||[]));selectedPadId.value=pads.value[0]?.id||'';await generate()}
async function download(){try{const r=await request('/api/export/svg',{method:'POST',body:JSON.stringify({...dimensions.value,pads:pads.value})});const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=`展开图-${dimensions.value.length}x${dimensions.value.width}x${dimensions.value.height}.svg`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('SVG 已导出')}catch{notify('导出失败',true)}}
function stopAnimation(){cancelAnimationFrame(animation)}
function animate(){cancelAnimationFrame(animation);const start=performance.now(),from=unfold.value,to=from>50?0:100;function step(t:number){const p=Math.min((t-start)/1100,1);unfold.value=from+(to-from)*(p*p*(3-2*p));if(p<1)animation=requestAnimationFrame(step)}animation=requestAnimationFrame(step)}
function preset(l:number,w:number,h:number){input.value={length:l,width:w,height:h,thickness:input.value.thickness};generate()}
onMounted(async()=>{try{await request('/api/health');online.value=true}catch{notify('后端或数据库未连接，请运行启动脚本',true)}await generate();if(online.value)await refresh()})
onBeforeUnmount(()=>{clearTimeout(noticeTimer);cancelAnimationFrame(animation)})
</script>
<template>
 <div class="app-shell">
  <aside class="rail"><a class="brand-icon" href="#" aria-label="Fold Studio 首页"><Layers3 :size="26"/></a><button class="rail-button active" aria-label="设计工作台"><Box :size="22"/></button><div class="rail-bottom"><span class="avatar">F</span></div></aside>
  <div class="main-shell">
   <header><a href="#" class="wordmark">fold<span>studio</span><small>BETA</small></a><div class="header-right"><span :class="['connection',online?'connected':'']"><i/>{{online?'本地工作空间已连接':'本地服务未连接'}}</span><span class="divider"/><span class="version">V 1.0</span></div></header>
   <main>
    <div class="heading"><div><div class="eyebrow">WORKSPACE / 01</div><h1>让尺寸，变得立体<span>。</span></h1><p>从一个长方体开始，探索每一面的展开方式。</p></div><div class="heading-tag"><span/> 参数化设计工作台</div></div>
    <div class="workspace">
     <section class="panel parameters"><div class="section-title"><h2><span class="step">01</span> 设置尺寸</h2><span class="unit">MM</span></div><p class="section-note">定义你的长方体，剩下的交给几何。</p>
      <div class="shape-type"><Box :size="23"/><div><strong>长方体</strong><small>RECTANGULAR PRISM</small></div><Check :size="17" class="selected-check"/></div>
      <div v-for="(label,key) in {length:'长度',width:'宽度',height:'高度'}" :key="key" class="dimension-field"><label :for="key">{{label}} <span>{{ {length:'L',width:'W',height:'H'}[key] }}</span></label><div class="number-input"><input :id="key" v-model.number="input[key]" type="number" min="1" max="10000" step="1" @keyup.enter="generate"/><span>mm</span></div></div>
      <div class="dimension-field"><label for="thickness">板材厚度 <span>T</span></label><div class="number-input"><input id="thickness" v-model.number="input.thickness" type="number" min="0" max="1000" step="0.1" @keyup.enter="generate"/><span>mm</span></div></div>
      <p class="section-note">长宽高为外尺寸；板厚 0 表示线框。内腔各尺寸扣除两倍板厚，展开图自动加入接缝边和折弯补偿。</p>
      <p v-if="!valid" class="validation">外尺寸 1–10000 mm；板厚 0–1000 mm 且小于最短边的一半</p>
      <button class="primary generate" :disabled="busy||!valid" @click="generate"><Layers3 :size="17"/>{{busy?'正在生成…':'生成展开图'}}<ArrowUpRight :size="17"/></button>
      <div class="presets"><span class="tiny-label">快速试试</span><div><button @click="preset(100,100,100)">正方体</button><button @click="preset(240,160,100)">收纳盒</button><button @click="preset(300,200,50)">扁平盒</button></div></div>
      <div class="tip"><CircleHelp :size="16"/><p>所有尺寸以毫米为单位。展开图为外表面示意，标注板厚；不含拼接、折弯和裁切补偿。</p></div>
     </section>
     <section class="panel canvas-panel"><div class="canvas-toolbar"><div class="tabs"><button :class="{selected:tab==='3d'}" @click="tab='3d'"><Box :size="16"/>立体预览</button><button :class="{selected:tab==='2d'}" @click="tab='2d'"><Layers3 :size="16"/>平面展开</button></div><button class="icon-button" title="重置视角" @click="scene?.reset();unfold=0"><RotateCcw :size="17"/></button></div>
      <div class="viewport"><div class="canvas-caption"><span class="live-dot"/>{{tab==='3d'?'透视视图 / PERSPECTIVE':'展开视图 / FLAT NET'}}</div><span v-if="geometry" class="dimension-chip">{{dimensions.length}} × {{dimensions.width}} × {{dimensions.height}} mm</span>
       <BoxScene v-if="geometry" v-show="tab==='3d'" ref="scene" :dimensions="dimensions" :unfold="unfold" :pads="visiblePads" :selected-pad-id="selectedPadId" @select-pad="selectedPadId=$event"/>
       <NetView v-if="geometry&&tab==='2d'" :geometry="geometry" :pads="visiblePads" :selected-id="selectedPadId" @select="selectedPadId=$event"/>
       <div v-if="!geometry" class="empty-canvas">输入尺寸，生成你的第一个展开图</div>
       <div class="canvas-legend"><span><i/>{{tab==='3d'?'可折叠面':'裁切线'}}</span><span><i class="dashed"/>{{tab==='3d'?'六面联动':'折叠线'}}</span></div><div class="orientation">Y ↑<br/>Z ↙ &nbsp; → X</div>
      </div>
      <div class="fold-control"><div class="fold-label"><Move3d :size="18"/><strong>{{tab==='3d'?'展开程度':'展开尺寸'}}</strong></div><template v-if="tab==='3d'"><span class="range-end">折叠</span><input aria-label="展开程度" v-model.number="unfold" @input="stopAnimation" type="range" min="0" max="100"/><span class="range-end">展开</span><span class="percent">{{Math.round(unfold)}}%</span><button class="subtle" @click="animate">{{unfold>50?'收起':'展开'}}</button></template><span v-else class="net-size">{{geometry?.net_width}} × {{geometry?.net_height}} mm</span></div>
     </section>
    </div>
    <section class="panel pads-panel">
     <div class="saved-header"><div><h2><Box :size="18"/>垫块 / 垫点 <span>{{pads.length}} / 100</span></h2><p>可放在箱内、箱外或悬空；修改尺寸和坐标后实时更新。</p></div><button class="subtle" :disabled="!geometry||pads.length>=100" @click="addPad"><Plus :size="16"/>添加垫块</button></div>
     <div v-if="pads.length" class="pad-tabs"><button v-for="p in pads" :key="p.id" :class="['subtle',{active:selectedPadId===p.id}]" @click="selectedPadId=p.id;tab='3d'">{{p.name||'未命名垫块'}}</button></div>
     <div v-if="selectedPad" class="pad-editor">
      <label>名称<input v-model="selectedPad.name" aria-label="垫块名称" maxlength="100"/></label>
      <label v-for="(label,key) in {length:'长 L',width:'宽 W',height:'高 H'}" :key="key">{{label}} · mm<input v-model.number="selectedPad[key]" :aria-label="`垫块${label}`" type="number" min="1" max="10000" step="any"/></label>
      <label v-for="(label,key) in {x:'X 左右',y:'Y 高度',z:'Z 前后'}" :key="key">{{label}} · mm<input v-model.number="selectedPad[key]" :aria-label="`垫块${label}`" type="number" min="-100000" max="100000" step="any"/></label>
      <button class="subtle" @click="tab='3d';scene?.focusPad()">定位垫块</button><button class="icon-button" aria-label="删除选中垫块" @click="deletePad"><Trash2 :size="17"/></button>
     </div>
     <p class="pad-help">原点为箱体底面中心，X 向右、Y 向上、Z 向前。位置指垫块底面中心，支持负坐标。长沿 X、宽沿 Z、高沿 Y；展开箱体时垫块保持原位。平面图 / SVG 显示垫块在底面坐标系的投影，标出高度；边距按闭合箱体计算，负值表示超出内腔或与板材相交。</p>
     <p v-if="!padsValid" class="validation">名称不能为空；长宽高须为 1–10000 mm，坐标须为 −100000–100000 mm。</p>
    </section>
    <div class="lower-grid"><section class="panel metrics"><div><span class="tiny-label">SURFACE AREA · 表面积</span><strong>{{geometry?(geometry.surface_area/100).toLocaleString('zh-CN',{maximumFractionDigits:2}):'—'}} <small>cm²</small></strong></div><div><span class="tiny-label">VOLUME · 体积</span><strong>{{geometry?(geometry.volume/1000).toLocaleString('zh-CN',{maximumFractionDigits:2}):'—'}} <small>cm³</small></strong></div><div><span class="tiny-label">FACES · 面数</span><strong>06 <small>个面 / 12 条棱</small></strong></div></section><section class="panel export-panel"><div><strong>将灵感带走</strong><p>导出带尺寸标注的矢量展开图</p></div><button class="export-button" :disabled="!geometry||!padsValid" @click="download"><Download :size="17"/>导出 SVG</button></section></div>
    <section class="panel saved-panel"><div class="saved-header"><div><h2>我的方案 <span>{{designs.length}}</span></h2><p>保存在本地 MySQL，随时继续设计。</p></div><div class="save-controls"><input v-model="name" maxlength="100" aria-label="方案名称" placeholder="输入方案名称"/><button class="subtle" :disabled="!geometry||saving||changed||!padsValid" @click="save"><Save :size="16"/>{{saving?'保存中…':changed?'请先生成':'保存当前方案'}}</button></div></div><div class="design-list"><div v-if="!designs.length" class="empty-state"><Plus :size="20"/><span>还没有保存的方案，留住你的第一个设计。</span></div><article v-for="d in designs" :key="d.id" class="design-card"><button class="design-open" @click="load(d)"><Box :size="23"/><div><strong>{{d.name}}</strong><small>{{d.length}} × {{d.width}} × {{d.height}} mm</small></div></button><button class="icon-button" :aria-label="`删除${d.name}`" @click="remove(d.id)"><Trash2 :size="15"/></button></article></div></section>
    <footer><span>FOLD STUDIO <i/> 把几何变成可能</span><span>拖动旋转视角 · 滚轮缩放 · 滑动展开</span></footer>
   </main>
  </div><div v-if="message" role="status" :class="['toast',{error:failed}]">{{message}}</div>
 </div>
</template>
