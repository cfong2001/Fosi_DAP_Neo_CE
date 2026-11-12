import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export type DisplayMode = 'theater' | 'eq' | 'bluetooth' | 'playlist' | 'lockscreen' | 'gapless' | 'opus' | 'system'
export type Display = { mode: DisplayMode; on: boolean; holding: boolean; progress: number; cover: number }
const CURVE = [-1, 0, 0, 1, 0, 0, 0, -1, -2, -1, -2, -1, -2, 0, 0, -1, -1, -1, -3, -1, 1, 0, -3, -1, -2, -2, 3, 5, -11, -7, -12]
const COVERS = [['#ed9b35', '#4b1914', '#63360c'], ['#3096b0', '#153b60', '#123d50'], ['#b9b17b', '#25483e', '#384937']]

function roundRect(w: number, h: number, r: number) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2
  s.moveTo(x+r,y); s.lineTo(x+w-r,y); s.quadraticCurveTo(x+w,y,x+w,y+r)
  s.lineTo(x+w,y+h-r); s.quadraticCurveTo(x+w,y+h,x+w-r,y+h)
  s.lineTo(x+r,y+h); s.quadraticCurveTo(x,y+h,x,y+h-r)
  s.lineTo(x,y+r); s.quadraticCurveTo(x,y,x+r,y)
  return s
}

/** An illustrative screen texture, never presented as a hardware capture. */
function paint(ctx: CanvasRenderingContext2D, state: Display) {
  const { mode, on, progress, cover } = state
  const w=480, h=560
  ctx.clearRect(0,0,w,h)
  ctx.fillStyle=mode==='theater' && on ? COVERS[cover][2] : '#101d22'
  ctx.fillRect(0,0,w,h)
  const text=(value:string,x:number,y:number,size=34,color='#e7f5f3',align:CanvasTextAlign='left')=>{
    ctx.font=`${size>=42 ? 600 : 400} ${size}px Barlow, sans-serif`;ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(value,x,y)
  }
  text(mode==='bluetooth' ? (on?'BT ON':'BT OFF') : 'CE / DAP NEO',28,43,28,'#abc6c9')
  text('▰',450,43,28,'#a5d7be','right')
  if(mode==='bluetooth') {
    text('Bluetooth',240,143,44,'#eef8f5','center')
    text(on?'ON':'OFF',240,278,112,on?'#91e4d3':'#84999d','center')
    ctx.fillStyle='#314348';ctx.fillRect(65,343,350,8)
    ctx.fillStyle='#ecab61';ctx.fillRect(65,343,350*progress,8)
    text(state.holding?'Holding Power…':on?'Ready to pair':'Module off',240,410,34,'#e1eae6','center')
    text('Long press / Power',240,498,30,'#a9c3c6','center')
  } else if(mode==='eq') {
    text('Heavy Metal',28,108,42)
    text(on?'HD 600 / fitted':'Stock preset',28,152,32,'#9fc5c8')
    ctx.lineWidth=1;ctx.strokeStyle='#456067'
    for(let y=210;y<=410;y+=50){ctx.beginPath();ctx.moveTo(28,y);ctx.lineTo(452,y);ctx.stroke()}
    ctx.beginPath();ctx.lineWidth=5;ctx.strokeStyle='#8de5d1'
    CURVE.forEach((v,i)=>{const x=28+i*424/30,y=310-v*progress*8; i?ctx.lineTo(x,y):ctx.moveTo(x,y)})
    ctx.stroke();text('20 Hz',28,459,29,'#abc6c9');text('20 kHz',452,459,29,'#abc6c9','right')
    text('31 bands / ±12 dB',240,522,30,'#d4e4df','center')
  } else if(mode==='theater') {
    // CE artwork: a centered cover with rounded corners (radius 10 of 144
    // on the device) and a rounded format badge on its lower-right corner.
    const [a,b]=COVERS[cover], gradient=ctx.createLinearGradient(100,85,380,345)
    gradient.addColorStop(0,a);gradient.addColorStop(1,b);ctx.fillStyle=gradient
    ctx.save();ctx.beginPath();ctx.roundRect(113,62,254,240,18);ctx.clip();ctx.fillRect(113,62,254,240)
    ctx.fillStyle='#f8dbad';ctx.beginPath();ctx.arc(290,184,44,0,Math.PI*2);ctx.fill();ctx.restore()
    ctx.fillStyle='#10161a';ctx.beginPath();ctx.roundRect(258,260,99,34,17);ctx.fill()
    text(['FLAC','MP3','OPUS'][cover],270,286,24,'#ffffff')
    text(['Evening light','Open water','Forest floor'][cover],240,346,39,'#f5f1e5','center')
    text('Sample artwork',240,382,30,'#cddbd1','center')
    // Elapsed and total time sit on their own line above the progress bar.
    text('01:24',28,422,26);text('04:13',452,422,26,'#d3dfd9','right')
    ctx.fillStyle='#ffffff44';ctx.fillRect(28,440,424,5);ctx.fillStyle='#fff';ctx.fillRect(28,440,154,5)
    // The CE transport glyphs, drawn straight over the derived background
    // (no dark tiles behind them): previous, play, next.
    ctx.fillStyle='#f5f1e5'
    const tri=(x:number,y:number,s:number,dir:1|-1)=>{ctx.beginPath();ctx.moveTo(x-dir*s*.5,y-s*.6);ctx.lineTo(x+dir*s*.6,y);ctx.lineTo(x-dir*s*.5,y+s*.6);ctx.closePath();ctx.fill()}
    tri(140,515,26,-1);ctx.fillRect(116,499,6,32)
    tri(244,515,38,1)
    tri(340,515,26,1);ctx.fillRect(358,499,6,32)
  } else if(mode==='playlist') {
    text('Evening.m3u',28,119,43)
    ;['Evening light','Open water','Last train'].forEach((t,i)=>{
      if(i===(on?1:0)){ctx.fillStyle='#306969';ctx.fillRect(18,155+i*92,444,80)}
      text(`${String(i+1).padStart(2,'0')} / ${t}`,30,206+i*92,34)
    })
    text('3 tracks / playlist',28,510,31,'#abc6c9')
  } else if(mode==='lockscreen') {
    text('HOLD ENABLED',240,130,31,'#abc6c9','center')
    text(on?'Evening light':'Playback',240,239,43,'#eef8f5','center')
    // The lock routine draws the title, then elapsed / total time
    text(on?'01:24 / 04:13':'—:— / —:—',240,345,58,'#91e4d3','center')
    text('Elapsed / total',240,430,32,'#abc6c9','center')
  } else if(mode==='gapless') {
    text(on?'Track 02.flac':'Track 01.flac',240,150,40,'#eef8f5','center')
    for(let i=0;i<27;i++){ctx.fillStyle='#8de5d1';const hh=24+(i*31)%116;ctx.fillRect(30+i*16,290-hh/2,9,hh)}
    text('Same-format playback',240,435,32,'#abc6c9','center')
  } else if(mode==='opus') {
    text('Opus playback',240,170,45,'#eef8f5','center');text('.opus',240,310,92,'#91e4d3','center');text('Standard image',240,440,34,'#abc6c9','center')
  } else {
    text('Wheel timer',240,170,43,'#eef8f5','center');text(on?'1,000':'2,500',240,310,88,'#91e4d3','center');text('wakeups / second',240,430,33,'#abc6c9','center')
  }
}

export default function PlayerModel({ state, onHoldStart, onHoldEnd }: { state: Display; onHoldStart?: () => void; onHoldEnd?: () => void }) {
  const host=useRef<HTMLDivElement>(null)
  const latest=useRef(state);latest.current=state
  const handlers=useRef({onHoldStart,onHoldEnd});handlers.current={onHoldStart,onHoldEnd}
  const refresh=useRef<()=>void>(()=>{})
  useEffect(()=>{
    const el=host.current;if(!el)return
    let renderer: THREE.WebGLRenderer
    try {renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true})}
    catch {el.dataset.unavailable='true';return}
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace
    const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(32,1,.1,30)
    const closeup = ['eq','lockscreen'].includes(latest.current.mode)
    const distance = closeup ? 4.8 : latest.current.mode === 'theater' ? 6.4 : 6.8
    const focus = closeup ? .6 : .05
    camera.position.set(0,focus,distance);camera.lookAt(0,focus,0)
    scene.add(new THREE.HemisphereLight(0xf1f7ff,0x52606c,3))
    const light=new THREE.DirectionalLight(0xffffff,4);light.position.set(-3,5,6);scene.add(light)
    const rim=new THREE.DirectionalLight(0xc7e5ff,2);rim.position.set(4,0,-2);scene.add(rim)
    const group=new THREE.Group();scene.add(group);group.rotation.set(.06,-.32,-.10)
    const silver=new THREE.MeshStandardMaterial({color:0xc4cdd3,metalness:.7,roughness:.34})
    const dark=new THREE.MeshStandardMaterial({color:0x141b20,metalness:.35,roughness:.45})
    const body=new THREE.Mesh(new THREE.ExtrudeGeometry(roundRect(1.82,3.4,.22),{depth:.15,bevelEnabled:true,bevelSegments:4,steps:1,bevelSize:.045,bevelThickness:.045}),silver)
    body.position.z=-.12;group.add(body)
    const bezel=new THREE.Mesh(new THREE.ShapeGeometry(roundRect(1.55,1.86,.17)),dark)
    bezel.position.set(0,.65,.084);group.add(bezel)
    const surface=document.createElement('canvas');surface.width=480;surface.height=560
    const ctx=surface.getContext('2d')!;const texture=new THREE.CanvasTexture(surface);texture.colorSpace=THREE.SRGBColorSpace
    const screen=new THREE.Mesh(new THREE.PlaneGeometry(1.32,1.54),new THREE.MeshBasicMaterial({map:texture}));screen.position.set(0,.65,.088);group.add(screen)
    const wheel=new THREE.Mesh(new THREE.CylinderGeometry(.61,.61,.025,80),dark);wheel.rotation.x=Math.PI/2;wheel.position.set(0,-.96,.095);group.add(wheel)
    const center=new THREE.Mesh(new THREE.CylinderGeometry(.23,.23,.035,64),new THREE.MeshStandardMaterial({color:0x343e46,roughness:.5,metalness:.4}));center.rotation.x=Math.PI/2;center.position.set(0,-.96,.12);group.add(center)
    const powerMaterial=new THREE.MeshStandardMaterial({color:0xed9b34,roughness:.3,metalness:.3,emissive:0xed9b34,emissiveIntensity:0})
    const power=new THREE.Mesh(new THREE.BoxGeometry(.085,.23,.1),powerMaterial);power.position.set(-.963,1.12,-.015);group.add(power)
    for(const y of [.58,.08]){const key=new THREE.Mesh(new THREE.BoxGeometry(.06,.31,.09),dark);key.position.set(-.95,y,-.015);group.add(key)}
    const port=new THREE.Mesh(new THREE.BoxGeometry(.3,.035,.065),dark);port.position.set(0,-1.72,0);group.add(port)
    // The large invisible hit volume is on the same physical button, not over the screen.
    const hit=new THREE.Mesh(new THREE.BoxGeometry(.43,.49,.6),new THREE.MeshBasicMaterial({visible:false}));hit.position.copy(power.position);group.add(hit)
    renderer.domElement.setAttribute('aria-hidden','true');el.append(renderer.domElement)
    const render=()=>{paint(ctx,latest.current);texture.needsUpdate=true;powerMaterial.emissiveIntensity=latest.current.holding?.7:0;renderer.render(scene,camera)}
    refresh.current=render
    const resize=()=>{const {width,height}=el.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();render()}
    const observer=new ResizeObserver(resize);observer.observe(el);resize()
    let active=false
    const down=(event:PointerEvent)=>{if(!handlers.current.onHoldStart)return;const rect=el.getBoundingClientRect();const ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1),camera);if(ray.intersectObject(hit).length){active=true;renderer.domElement.setPointerCapture(event.pointerId);handlers.current.onHoldStart();event.preventDefault()}}
    const up=()=>{if(active){active=false;handlers.current.onHoldEnd?.()}}
    renderer.domElement.addEventListener('pointerdown',down);renderer.domElement.addEventListener('pointerup',up);renderer.domElement.addEventListener('pointercancel',up);renderer.domElement.addEventListener('lostpointercapture',up)
    let alive=true;document.fonts.ready.then(()=>{if(alive)render()})
    return()=>{alive=false;observer.disconnect();refresh.current=()=>{};renderer.domElement.removeEventListener('pointerdown',down);renderer.domElement.removeEventListener('pointerup',up);renderer.domElement.removeEventListener('pointercancel',up);renderer.domElement.removeEventListener('lostpointercapture',up);scene.traverse(obj=>{if(obj instanceof THREE.Mesh){obj.geometry.dispose();const materials=Array.isArray(obj.material)?obj.material:[obj.material];materials.forEach(m=>m.dispose())}});texture.dispose();renderer.dispose();renderer.domElement.remove()}
  },[])
  useEffect(()=>{refresh.current()},[state])
  return <div className="player-model" ref={host} role="img" aria-label={state.mode === 'bluetooth' ? `DAP Neo screen: Bluetooth ${state.on ? 'on' : 'off'}${state.holding ? ', Power button held' : ''}` : state.mode === 'eq' ? `DAP Neo screen: ${state.on ? 'fitted HD 600 EQ curve' : 'stock EQ preset'}` : `DAP Neo ${state.mode} illustration`}><span className="player-model-fallback">3D preview unavailable. Use the controls below to preview the feature.</span></div>
}
