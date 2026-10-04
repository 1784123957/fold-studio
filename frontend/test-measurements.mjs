import { readFileSync } from 'node:fs'
import assert from 'node:assert/strict'
import ts from 'typescript'
const source=readFileSync(new URL('./src/measurements.ts',import.meta.url),'utf8')
const code=ts.transpile(source,{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022})
const {margins}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'))
const d={length:240,width:160,height:100}
const p={length:40,width:30,height:15,x:-65,y:20,z:10}
assert.deepEqual(margins(d,p),{左:35,右:165,后:75,前:55,底:20,顶:65})
for(const position of [{x:0,y:0,z:0},{x:150,y:-10,z:100},{x:-200,y:110,z:-100}]){
 const m=margins(d,{...p,...position})
 assert.equal(m.左+p.length+m.右,d.length)
 assert.equal(m.后+p.width+m.前,d.width)
 assert.equal(m.底+p.height+m.顶,d.height)
}
assert.equal(margins(d,{...p,x:150}).右,-50)
assert.equal(margins(d,{...p,y:0}).底,0)
console.log('PASS: exact edge clearances, contact, outside coordinates, dimension sums')

assert.deepEqual(margins({...d,thickness:5},p),{左:30,右:160,后:70,前:50,底:15,顶:60})
