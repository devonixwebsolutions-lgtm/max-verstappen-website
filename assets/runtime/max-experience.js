(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let disposeHead = () => {};

  function startIntro() {
    const loader = document.querySelector('[data-max-loader]');
    if (!loader) return;
    const car = loader.querySelector('[data-loader-car]');
    const name = loader.querySelector('[data-loader-name]');
    const caption = loader.querySelector('[data-loader-caption]');
    const photo = car.querySelector('img');
    const started = performance.now();
    let ready = false, running = true, introFrame = 0;
    document.documentElement.dataset.maxIntro = 'running';
    window.addEventListener('replica-runtime-error', () => { ready = true; }, {once:true});
    const finish = () => {
      running = false;
      loader.classList.add('is-complete');
      loader.setAttribute('aria-hidden', 'true');
      document.documentElement.dataset.maxIntro = 'complete';
      const original = document.querySelector('.transition-w');
      if (original) { original.style.visibility = 'hidden'; original.style.pointerEvents = 'none'; }
      window.lenisStart?.();
      window.dispatchEvent(new Event('max-intro-complete'));
      setTimeout(() => loader.remove(), reduced.matches ? 250 : 750);
    };
    const frame = now => {
      if (!running) return;
      const elapsed = now - started;
      const w = innerWidth, cw = car.getBoundingClientRect().width;
      const duration = reduced.matches ? 0 : 1850;
      const progress = reduced.matches ? 1 : Math.min(1, Math.max(0, (elapsed - 350) / duration));
      // Accelerating across the screen: the car's nose uncovers the red name.
      const eased = progress * progress * (3 - 2 * progress);
      const x = -cw - 20 + eased * (w + cw + 60);
      car.style.transform = `translate3d(${x}px,0,0)`;
      const bounds = name.getBoundingClientRect();
      const reveal = reduced.matches ? 1 : Math.min(1, Math.max(0, (x + cw - bounds.left) / bounds.width));
      name.style.clipPath = `inset(0 ${(1 - reveal) * 100}% 0 0)`;
      if (progress === 1) caption.textContent = 'AND AWAY WE GO.';
      const transition = document.querySelector('.transition-w');
      ready ||= document.documentElement.dataset.replicaRuntime === 'ready' ||
        (transition && getComputedStyle(transition).visibility === 'hidden');
      // A finite intro also protects the site if an optional reference effect fails.
      if (elapsed > (reduced.matches ? 450 : 2800) && (ready || elapsed > 6500) && (photo.complete || elapsed > 6500)) finish();
      else introFrame=requestAnimationFrame(frame);
    };
    introFrame=requestAnimationFrame(frame);
    // Background tabs should not become trapped by suspended animation frames.
    document.addEventListener('visibilitychange', () => {
      cancelAnimationFrame(introFrame);
      if (!document.hidden && running) introFrame=requestAnimationFrame(frame);
    });
  }

  function createRelief(canvas, headImage, helmetImage) {
    const gl = canvas.getContext('webgl', {alpha:true, antialias:true, premultipliedAlpha:false});
    if (!gl) return null;
    const shader = (type, source) => {
      const s = gl.createShader(type); gl.shaderSource(s, source); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { gl.deleteShader(s); throw new Error('Head shader failed'); }
      return s;
    };
    const vertex = shader(gl.VERTEX_SHADER, `
      precision highp float;
      attribute vec2 aUV;
      uniform vec2 uTurn;
      uniform mediump float uBlend;
      uniform float uAspect;
      varying mediump vec2 vUV;
      varying mediump float vShade;
      void main() {
        vec2 q = aUV * 2.0 - 1.0;
        float dome = sqrt(max(0.0, 1.0 - q.x*q.x/0.85 - q.y*q.y/1.2));
        float nose = exp(-q.x*q.x*55.0 - (q.y+0.03)*(q.y+0.03)*32.0) * 0.18;
        float depth = mix(dome*0.3 + nose, dome*0.5, uBlend);
        vec3 p = vec3(q.x, q.y*1.25, depth);
        float sy = sin(uTurn.x), cy = cos(uTurn.x);
        float sx = sin(uTurn.y), cx = cos(uTurn.y);
        p = vec3(p.x*cy+p.z*sy, p.y, -p.x*sy+p.z*cy);
        p = vec3(p.x, p.y*cx-p.z*sx, p.y*sx+p.z*cx);
        float w = 4.0-p.z;
        gl_Position = vec4(p.x*2.8/uAspect, p.y*2.8, (w-2.0)*0.5, w);
        vUV = aUV;
        vShade = 1.0 + 0.04*(q.x*uTurn.x-q.y*uTurn.y);
      }
    `);
    const fragment = shader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      uniform sampler2D uHead, uHelmet;
      uniform float uBlend;
      uniform vec2 uHeadFit, uHelmetFit;
      varying mediump vec2 vUV;
      varying mediump float vShade;
      vec4 fitted(sampler2D image, vec2 fit) {
        vec2 uv = (vUV-0.5)/fit+0.5;
        if (uv.x<0.0 || uv.x>1.0 || uv.y<0.0 || uv.y>1.0) return vec4(0.0);
        return texture2D(image, uv);
      }
      void main() {
        vec4 face = fitted(uHead,uHeadFit), helmet = fitted(uHelmet,uHelmetFit);
        float reveal = smoothstep(vUV.y,vUV.y+0.14,uBlend*1.14);
        float a = face.a*(1.0-reveal)+helmet.a*reveal;
        if (a < 0.02) discard;
        vec3 rgb = (face.rgb*face.a*(1.0-reveal)+helmet.rgb*helmet.a*reveal)/max(a,0.01);
        rgb *= vShade;
        gl_FragColor = vec4(rgb,a);
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex); gl.attachShader(program, fragment); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error('Head program failed');
    gl.useProgram(program);
    const columns=96, rows=112, uv=[], indexes=[];
    for(let y=0;y<=rows;y++) for(let x=0;x<=columns;x++) uv.push(x/columns,y/rows);
    for(let y=0;y<rows;y++) for(let x=0;x<columns;x++) {
      const a=y*(columns+1)+x,b=a+columns+1; indexes.push(a,a+1,b,a+1,b+1,b);
    }
    const vertices=gl.createBuffer(), indices=gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER,vertices); gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(uv),gl.STATIC_DRAW);
    const attribute=gl.getAttribLocation(program,'aUV'); gl.enableVertexAttribArray(attribute); gl.vertexAttribPointer(attribute,2,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(indexes),gl.STATIC_DRAW);
    const uniforms = Object.fromEntries(['uTurn','uBlend','uAspect','uHeadFit','uHelmetFit'].map(key=>[key,gl.getUniformLocation(program,key)]));
    const textures=[];
    for(const [i,img] of [headImage,helmetImage].entries()) {
      const texture=gl.createTexture(); textures.push(texture); gl.activeTexture(gl.TEXTURE0+i); gl.bindTexture(gl.TEXTURE_2D,texture);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      gl.uniform1i(gl.getUniformLocation(program,i ? 'uHelmet':'uHead'),i);
      const ratio=img.naturalWidth/img.naturalHeight, fit=ratio>0.8 ? [1,0.8/ratio]:[ratio/0.8,1];
      gl.uniform2f(uniforms[i ? 'uHelmetFit':'uHeadFit'],...fit);
    }
    gl.disable(gl.BLEND); gl.clearColor(0,0,0,0);
    return {
      render(x,y,blend) {
        const bounds=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,1.75);
        const w=Math.round(bounds.width*dpr),h=Math.round(bounds.height*dpr);
        if(!w||!h)return;
        if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}
        gl.clear(gl.COLOR_BUFFER_BIT); gl.uniform2f(uniforms.uTurn,x,y); gl.uniform1f(uniforms.uBlend,blend); gl.uniform1f(uniforms.uAspect,w/h);
        gl.drawElements(gl.TRIANGLES,indexes.length,gl.UNSIGNED_SHORT,0);
      },
      dispose() { textures.forEach(t=>gl.deleteTexture(t)); gl.deleteBuffer(vertices); gl.deleteBuffer(indices); gl.deleteProgram(program); gl.deleteShader(vertex); gl.deleteShader(fragment); }
    };
  }

  function initHead() {
    disposeHead();
    const stage=document.querySelector('[data-max-head]'); if(!stage)return;
    const face=stage.querySelector('.mv-head-face'),helmet=stage.querySelector('.mv-head-helmet'),canvas=stage.querySelector('canvas');
    let pinned=false,hovered=false,focused=false,visible=true,alive=true,renderer=null,raf=0;
    let targetX=0,targetY=0,x=0,y=0,blend=0;
    const abort=new AbortController(),opts={signal:abort.signal};
    const state=() => {
      const on=pinned||hovered||focused;
      stage.dataset.helmet=on?'on':'off'; stage.setAttribute('aria-pressed',String(on));
      stage.setAttribute('aria-label',on?'Show Max Verstappen’s head':'Show Max Verstappen’s helmet');
    };
    stage.addEventListener('pointerenter',e=>{if(e.pointerType!=='touch'){hovered=true;state();}},opts);
    stage.addEventListener('pointerleave',()=>{hovered=false;state();},opts);
    stage.addEventListener('focus',()=>{focused=stage.matches(':focus-visible');state();},opts);
    stage.addEventListener('blur',()=>{focused=false;state();},opts);
    stage.addEventListener('click',e=>{pinned=!pinned;hovered=false;focused=false;state();},opts);
    stage.addEventListener('keydown',e=>{if(e.key==='Escape'){pinned=false;hovered=false;focused=false;state();}},opts);
    document.addEventListener('pointermove',e=>{
      if(reduced.matches||e.pointerType==='touch')return;
      const r=stage.getBoundingClientRect(); targetX=Math.max(-1,Math.min(1,(e.clientX-r.left-r.width/2)/(innerWidth*.4)));
      targetY=Math.max(-1,Math.min(1,(e.clientY-r.top-r.height/2)/(innerHeight*.4)));
    },{...opts,passive:true});
    canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();stage.dataset.renderer='css';renderer=null;},opts);
    const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;},{threshold:0}); observer.observe(stage);
    const tick=now=>{
      if(!alive)return;
      if(visible&&!document.hidden){
        x+=(targetX-x)*.07;y+=(targetY-y)*.07;
        const target=stage.dataset.helmet==='on'?1:0; blend+=(target-blend)*(reduced.matches ? .5 : .07);
        if(Math.abs(target-blend)<.001)blend=target;
        stage.style.setProperty('--head-x',reduced.matches?'0':x.toFixed(4));stage.style.setProperty('--head-y',reduced.matches?'0':y.toFixed(4));
        stage.style.setProperty('--head-float',reduced.matches?'0':(Math.sin(now*.0008)*6).toFixed(2));
        renderer?.render(reduced.matches?0:x*.25,reduced.matches?0:y*.14,blend);
      }
      raf=requestAnimationFrame(tick);
    };
    Promise.all([face.decode(),helmet.decode()]).then(()=>{
      if(!alive)return;
      try{renderer=createRelief(canvas,face,helmet);if(renderer){renderer.render(0,0,blend);stage.dataset.renderer='webgl';}else stage.dataset.renderer='css';}
      catch{stage.dataset.renderer='css';}
    }).catch(()=>{stage.dataset.renderer='css';});
    raf=requestAnimationFrame(tick);
    disposeHead=()=>{alive=false;abort.abort();observer.disconnect();cancelAnimationFrame(raf);renderer?.dispose();};
  }
  const init=()=>{startIntro();initHead();};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
  window.addEventListener('page-transition-start',()=>disposeHead());
  window.addEventListener('page-transition-end',initHead);
})();
