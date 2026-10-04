import type { Dimensions, Pad } from './types'
export const format = (n:number|undefined|null) => Number((n??0).toFixed(2)).toString()
export function margins(d:Dimensions & {thickness?:number},p:Pad){const t=d.thickness??0;return {
 左:p.x-p.length/2+d.length/2-t,右:d.length/2-p.x-p.length/2-t,
 后:p.z-p.width/2+d.width/2-t,前:d.width/2-p.z-p.width/2-t,
 底:p.y-t,顶:d.height-p.y-p.height-t,
}}
export function projection(d:Dimensions & {net_origin?:number},p:Pad){const o=d.net_origin??0;return {x:o+d.height+d.length/2+p.x-p.length/2,y:o+d.height+1.5*d.width+p.z-p.width/2}}
