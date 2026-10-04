<script setup lang="ts">
import {computed} from 'vue'
import type {Geometry,Pad} from '../types'
import {projection,format} from '../measurements'
const props=defineProps<{geometry:Geometry;pads:Pad[];selectedId:string}>()
defineEmits<{select:[id:string]}>()
const projected=computed(()=>props.pads.map(p=>({...p,...projection(props.geometry,p)})))
const bounds=computed(()=>{const ps=projected.value;const minX=Math.min(0,...ps.map(p=>p.x)),minY=Math.min(0,...ps.map(p=>p.y));const maxX=Math.max(props.geometry.net_width,...ps.map(p=>p.x+p.length)),maxY=Math.max(props.geometry.net_height,...ps.map(p=>p.y+p.width));const pad=Math.max(maxX-minX,maxY-minY)*.16;return `${minX-pad} ${minY-pad} ${maxX-minX+2*pad} ${maxY-minY+2*pad}`})
const font=computed(()=>Math.max(props.geometry.net_width,props.geometry.net_height)*.019)
const thickness=computed(()=>props.geometry.thickness||0)
</script>
<template>
 <svg class="net-svg" :viewBox="bounds" aria-label="含垫块投影的平面展开图">
  <g v-for="f in geometry.faces" :key="f.id"><rect :x="f.x" :y="f.y" :width="f.width" :height="f.height" fill="#edf4ff" stroke="#5580ae" :stroke-width="font*.07"/><rect v-if="thickness>0 && f.width>2*thickness && f.height>2*thickness" :x="f.x+thickness" :y="f.y+thickness" :width="f.width-2*thickness" :height="f.height-2*thickness" fill="none" stroke="#8aa2bd" :stroke-width="font*.045" stroke-dasharray="4 3"/><text :x="f.x+f.width/2" :y="f.y+font*1.5" text-anchor="middle" :font-size="font" fill="#355b80">{{f.label}} {{f.width}} × {{f.height}}</text></g>
  <g v-for="(f,i) in geometry.folds" :key="i"><path :d="`M${f[0]},${f[1]} L${f[2]},${f[3]}`" stroke="#edf4ff" :stroke-width="font*.2"/><path :d="`M${f[0]},${f[1]} L${f[2]},${f[3]}`" stroke="#377fec" :stroke-width="font*.09" :stroke-dasharray="`${font*.4} ${font*.25}`"/></g>
  <g v-for="(p,i) in projected" :key="p.id" role="button" tabindex="0" :aria-label="`选择${p.name}投影`" @click="$emit('select',p.id)" @keydown.enter="$emit('select',p.id)" style="cursor:pointer">
   <rect :x="p.x" :y="p.y" :width="p.length" :height="p.width" :fill="p.id===selectedId?'#ffc879':'#8cd0be'" fill-opacity=".65" stroke="#b87924" :stroke-width="font*.12" :stroke-dasharray="`${font*.35} ${font*.15}`"/>
   <text :x="p.x+p.length/2" :y="p.y+p.width/2" text-anchor="middle" dominant-baseline="middle" :font-size="font*.9" fill="#8a5312">{{i+1}}</text>
  </g>
 </svg>
 <div class="net-pad-key"><strong>板厚 t = {{format(thickness)}} mm · 接缝边 = {{format(geometry.seam_allowance)}} mm · 折弯补偿 = {{format(geometry.bend_allowance)}} mm</strong><template v-if="pads.length"><button v-for="(p,i) in pads" :key="p.id" @click="$emit('select',p.id)">{{i+1}} · {{p.name}}：{{format(p.length)}} × {{format(p.width)}} × {{format(p.height)}}；底高 {{format(p.y)}}</button></template></div>
</template>
