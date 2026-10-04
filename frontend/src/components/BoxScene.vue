<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref, computed } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { margins, format } from '../measurements'
import type { BoxDimensions, Pad } from '../types'
const props = defineProps<{ dimensions: BoxDimensions; unfold: number; pads: Pad[]; selectedPadId:string }>()
const emit=defineEmits<{ 'select-pad':[id:string] }>()
let padGroup: THREE.Group
const host = ref<HTMLDivElement>()
const selected=computed(()=>props.pads.find(p=>p.id===props.selectedPadId))
const gaps=computed(()=>selected.value?margins(props.dimensions,selected.value):null)
const labels=ref<{text:string;x:number;y:number;color:string;anchorX:number;anchorY:number}[]>([])
let dimensionsGroup:THREE.Group
let anchors:{text:string;point:THREE.Vector3;color:string}[]=[]
function clearDimensions(){if(!dimensionsGroup)return;dimensionsGroup.traverse(o=>{if(o instanceof THREE.Line){o.geometry.dispose();(o.material as THREE.Material).dispose()}});scene.remove(dimensionsGroup)}
function buildDimensions(){
 if(!scene)return
 clearDimensions();dimensionsGroup=new THREE.Group();scene.add(dimensionsGroup);anchors=[]
 const d=props.dimensions,s=3/Math.max(d.length,d.width,d.height),l=d.length/2,w=d.width/2,h=d.height
 function measure(a:number[],b:number[],text:string,color:string){
  const points=[a,b].map(v=>new THREE.Vector3(v[0]!*s,v[1]!*s+.025,v[2]!*s))
  const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineDashedMaterial({color,dashSize:.06,gapSize:.035,depthTest:false}));line.computeLineDistances();line.renderOrder=5;dimensionsGroup.add(line)
  const direction=points[1]!.clone().sub(points[0]!);const tick=new THREE.Vector3(0,.045,0)
  if(Math.abs(direction.y)>Math.abs(direction.x)+Math.abs(direction.z))tick.set(.045,0,0)
  for(const point of points){const cap=new THREE.Line(new THREE.BufferGeometry().setFromPoints([point.clone().sub(tick),point.clone().add(tick)]),new THREE.LineBasicMaterial({color,depthTest:false}));cap.renderOrder=6;dimensionsGroup.add(cap)}
  anchors.push({text,point:points[0]!.clone().lerp(points[1]!,.5),color})
 }
 measure([-l,0,w+15],[l,0,w+15],`${format(d.length)} mm`,'#356bb1')
 measure([l+15,0,-w],[l+15,0,w],`${format(d.width)} mm`,'#356bb1')
 measure([l+15,0,-w],[l+15,h,-w],`${format(h)} mm`,'#356bb1')
 const p=selected.value
 if(p&&props.unfold===0){const x0=p.x-p.length/2,x1=p.x+p.length/2,z0=p.z-p.width/2,z1=p.z+p.width/2,y=p.y+p.height;const m=margins(d,p),t=d.thickness
  measure([x0,y,z1],[x1,y,z1],`${format(p.length)} mm`,'#167e76')
  measure([x1,y,z0],[x1,y,z1],`${format(p.width)} mm`,'#167e76')
  measure([x1,p.y,z1],[x1,y,z1],`${format(p.height)} mm`,'#167e76')
  measure([-l+t,p.y,p.z],[x0,p.y,p.z],`${format(m.左)} mm`,'#a16b19')
  measure([x1,p.y,p.z],[l-t,p.y,p.z],`${format(m.右)} mm`,'#a16b19')
  measure([p.x,p.y,-w+t],[p.x,p.y,z0],`${format(m.后)} mm`,'#a16b19')
  measure([p.x,p.y,z1],[p.x,p.y,w-t],`${format(m.前)} mm`,'#a16b19')
  measure([p.x,t,p.z],[p.x,p.y,p.z],`${format(m.底)} mm`,'#a16b19')
  measure([p.x,y,p.z],[p.x,h-t,p.z],`${format(m.顶)} mm`,'#a16b19')
 }
 dimensionsGroup.visible=props.unfold===0
}
function projectLabels(){
 if(!host.value||props.unfold!==0){labels.value=[];return}
 const width=host.value.clientWidth,height=host.value.clientHeight
 const placed:{text:string;x:number;y:number;color:string;anchorX:number;anchorY:number}[]=[]
 for(const a of anchors){
  const v=a.point.clone().project(camera)
  if(v.z< -1||v.z>1||Math.abs(v.x)>1||Math.abs(v.y)>1)continue
  const x=(v.x+1)*width/2,y=(1-v.y)*height/2
  placed.push({text:a.text,x,y,anchorX:x,anchorY:y,color:a.color})
 }
 labels.value=placed
}
const error = ref('')
let renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera, controls: OrbitControls
let root: THREE.Group, back: THREE.Group, front: THREE.Group, left: THREE.Group, right: THREE.Group, lid: THREE.Group
let resize: ResizeObserver, frame = 0
function panel(w:number,h:number,x:number,y:number,z:number, parent:THREE.Group,color:number, horizontal=false, axis:'x'|'z'='z') {
  const t=props.dimensions.thickness*3/Math.max(props.dimensions.length,props.dimensions.width,props.dimensions.height)
  const geometry = t>0?(horizontal?new THREE.BoxGeometry(w,t,h):axis==='x'?new THREE.BoxGeometry(t,h,w):new THREE.BoxGeometry(w,h,t)):new THREE.PlaneGeometry(w,h)
  if(t>0&&horizontal)geometry.translate(0,t/2,0)
  else if(t===0){
    if(horizontal) geometry.rotateX(-Math.PI/2)
    else if(axis==='x') geometry.rotateY(Math.PI/2)
  }
  const mesh = new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,transparent:true,opacity:.12,depthWrite:false}))
  mesh.position.set(x,y,z); parent.add(mesh)
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry),new THREE.LineBasicMaterial({color:0x497fb6}))
  edges.position.copy(mesh.position);parent.add(edges)
}
function disposeRoot() {
  if (!root) return
  root.traverse(o=> { if (o instanceof THREE.Mesh || o instanceof THREE.LineSegments) { o.geometry.dispose(); const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>m.dispose()) } })
  scene.remove(root)
}
function build() {
  if (!scene) return
  disposeRoot();root = new THREE.Group();scene.add(root)
  const scale = 3 / Math.max(props.dimensions.length,props.dimensions.width,props.dimensions.height)
  const l=props.dimensions.length*scale,w=props.dimensions.width*scale,h=props.dimensions.height*scale
  const t=props.dimensions.thickness*scale
  root.position.y=.025
  // A zero-thickness model is a closed wireframe box. Using one box geometry
  // avoids six independent planes drifting apart at the folded position.
  if (t === 0) {
    const box = new THREE.BoxGeometry(l,h,w)
    box.translate(0,h/2,0)
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(box),new THREE.LineBasicMaterial({color:0x497fb6}))
    root.add(edges)
    buildPads(); buildDimensions(); return
  }
  // Solid closed-box mode: build six independent boards in outer coordinates.
  // Keeping every board in root space avoids compounded parent rotations and
  // remains correct when the board thickness is a large fraction of H/W.
  const addBoard=(sx:number,sy:number,sz:number,x:number,y:number,z:number,color:number)=>{
    const g=new THREE.BoxGeometry(sx,sy,sz)
    const mesh=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,transparent:true,opacity:.2,depthWrite:false}))
    mesh.position.set(x,y,z);root.add(mesh)
    const edge=new THREE.LineSegments(new THREE.EdgesGeometry(g),new THREE.LineBasicMaterial({color:0x497fb6}));edge.position.copy(mesh.position);root.add(edge)
  }
  addBoard(l,t,w,0,t/2,0,0x5c95db)
  addBoard(l,t,w,0,h-t/2,0,0x7c9df0)
  addBoard(l,h-2*t,t,0,h/2,w/2-t/2,0x6ba9db)
  addBoard(l,h-2*t,t,0,h/2,-w/2+t/2,0x72a5da)
  addBoard(t,h-2*t,w-2*t,-l/2+t/2,h/2,0,0x91a9cf)
  addBoard(t,h-2*t,w-2*t,l/2-t/2,h/2,0,0x91a9cf)
  buildPads();buildDimensions();return;
  panel(l,w,0,0,0,root,0x5c95db,true)
  back=new THREE.Group();back.position.z=-w/2+t/2;root.add(back);panel(l,Math.max(h-2*t,.001),0,h/2,0,back,0x72a5da,false,'z')
  lid=new THREE.Group();lid.position.z=-h;back.add(lid);panel(l,w,0,0,-w/2,lid,0x7c9df0,true)
  front=new THREE.Group();front.position.z=w/2-t/2;root.add(front);panel(l,Math.max(h-2*t,.001),0,h/2,0,front,0x6ba9db,false,'z')
  left=new THREE.Group();left.position.x=-l/2+t/2;root.add(left);panel(Math.max(h-2*t,.001),w,0,h/2,0,left,0x91a9cf,false,'x')
  right=new THREE.Group();right.position.x=l/2-t/2;root.add(right);panel(Math.max(h-2*t,.001),w,0,h/2,0,right,0x91a9cf,false,'x')
  buildPads();fold()
}
function clearPads(){
 if(!padGroup)return
 padGroup.traverse(o=>{if(o instanceof THREE.Mesh||o instanceof THREE.LineSegments){o.geometry.dispose();const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>m.dispose())}})
 scene.remove(padGroup)
}
function buildPads(){
 if(!scene)return
 clearPads();padGroup=new THREE.Group();scene.add(padGroup)
 const scale=3/Math.max(props.dimensions.length,props.dimensions.width,props.dimensions.height)
 for(const p of props.pads){
  const g=new THREE.BoxGeometry(p.length*scale,p.height*scale,p.width*scale)
  const selected=p.id===props.selectedPadId
  const mesh=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color:selected?0xf4ab4c:0x6ab7ab,transparent:true,opacity:.65}))
  mesh.position.set(p.x*scale,(p.y+p.height/2)*scale+.025,p.z*scale);mesh.userData.padId=p.id;padGroup.add(mesh)
  const edges=new THREE.LineSegments(new THREE.EdgesGeometry(g),new THREE.LineBasicMaterial({color:selected?0xc57719:0x328778}));edges.position.copy(mesh.position);padGroup.add(edges)
 }
}
let downX=0,downY=0
function pointerDown(e:PointerEvent){downX=e.clientX;downY=e.clientY}
function select(e:PointerEvent){
 if(Math.hypot(e.clientX-downX,e.clientY-downY)>5||!padGroup)return
 const rect=renderer.domElement.getBoundingClientRect(),ray=new THREE.Raycaster()
 ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera)
 const hit=ray.intersectObjects(padGroup.children).find(h=>h.object.userData.padId)
 if(hit)emit('select-pad',hit.object.userData.padId)
}
function focusPad(){
 const p=props.pads.find(p=>p.id===props.selectedPadId);if(!p||!camera)return
 const scale=3/Math.max(props.dimensions.length,props.dimensions.width,props.dimensions.height)
 const center=new THREE.Vector3(p.x*scale,(p.y+p.height/2)*scale+.025,p.z*scale)
 const distance=Math.max(p.length,p.width,p.height)*scale*3
 controls.minDistance=.01;controls.maxDistance=Math.max(30,distance*4);camera.far=Math.max(200,distance*10);camera.updateProjectionMatrix()
 controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,.8,1).normalize().multiplyScalar(Math.max(distance,.1)));controls.update()
}
function fold() {
  if(!back)return
  const angle = (1-props.unfold/100)*Math.PI/2
  back.rotation.x=angle;lid.rotation.x=angle;front.rotation.x=-angle;left.rotation.z=-angle;right.rotation.z=angle
  buildDimensions()
}
function reset() { camera?.position.set(7,6,8);controls?.target.set(0,.6,0);controls?.update() }
defineExpose({reset,focusPad})
onMounted(()=>{
 try {
  scene=new THREE.Scene();scene.background=new THREE.Color('#f7f9fc')
  camera=new THREE.PerspectiveCamera(38,1,.01,200)
  renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.value!.appendChild(renderer.domElement)
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=3;controls.maxDistance=30;controls.maxPolarAngle=Math.PI*.49;reset()
  const grid=new THREE.GridHelper(30,60,0xdde5ef,0xe8edf4);scene.add(grid)
  renderer.domElement.addEventListener('pointerdown',pointerDown);renderer.domElement.addEventListener('pointerup',select)
  build()
  resize=new ResizeObserver(()=>{const w=host.value!.clientWidth,h=host.value!.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()});resize.observe(host.value!)
  const animate=()=>{frame=requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);projectLabels()};animate()
 } catch {error.value='浏览器未启用 WebGL，请开启硬件加速后重试。'}
})
watch(()=>[props.pads,props.selectedPadId],()=>{buildPads();buildDimensions()},{deep:true})
watch(()=>props.dimensions,build,{deep:true});watch(()=>props.unfold,fold)
onBeforeUnmount(()=>{cancelAnimationFrame(frame);renderer?.domElement.removeEventListener('pointerdown',pointerDown);renderer?.domElement.removeEventListener('pointerup',select);clearPads();clearDimensions();resize?.disconnect();controls?.dispose();disposeRoot();scene?.traverse(o=>{if(o instanceof THREE.LineSegments){o.geometry.dispose();(o.material as THREE.Material).dispose()}});renderer?.dispose()})
</script>
<template><div ref="host" class="scene"><div class="dimension-labels"><span v-for="(label,i) in labels" :key="i" :style="{left:label.x+'px',top:label.y+'px',color:label.color}">{{label.text}}</span></div>
<div class="measurement-card"><strong>尺寸标注 · mm</strong><p>箱体 L {{format(dimensions.length)}} / W {{format(dimensions.width)}} / H {{format(dimensions.height)}}</p><p>板厚 {{format(dimensions.thickness)}} mm · 内腔 {{format(dimensions.length-2*dimensions.thickness)}} × {{format(dimensions.width-2*dimensions.thickness)}} × {{format(dimensions.height-2*dimensions.thickness)}} mm</p><template v-if="selected"><strong>{{selected.name}}</strong><p>长 {{format(selected.length)}} · 宽 {{format(selected.width)}} · 高 {{format(selected.height)}}</p><div class="gap-grid"><span v-for="(value,key) in gaps" :key="key" :class="{outside:value<0}">{{key}}边距 {{format(value)}}</span></div></template><small>{{unfold>0?'展开中：边距按闭合箱体计算':'蓝：箱体 · 绿：垫块 · 橙：边距；方向固定于坐标轴，负值表示超出'}}</small></div>
<p v-if="error" class="scene-error">{{error}}</p></div></template>
