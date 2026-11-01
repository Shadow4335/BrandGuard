/* GPU wave flow: one texture, bounded resolution, no per-frame DOM updates. */
function initSilverWaveFlow(){
  const host=document.querySelector('.silver-bg');
  if(!host)return ()=>{};
  const preference=matchMedia('(prefers-reduced-motion: reduce)');
  const canvas=document.createElement('canvas');canvas.className='silver-wave-canvas';canvas.setAttribute('aria-hidden','true');host.appendChild(canvas);
  const gl=canvas.getContext('webgl',{alpha:false,antialias:false,depth:false,stencil:false,preserveDrawingBuffer:false,powerPreference:'low-power'});
  if(!gl){canvas.remove();return ()=>{}}
  let dead=false,ready=false,visible=true,frame=0,last=0,elapsed=0,program,texture,buffer,vertex,fragment;
  const compact=matchMedia('(max-width:760px)').matches;
  const interval=1000/(compact?30:60);
  function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){gl.deleteShader(s);throw new Error('Wave shader unavailable')}return s}
  let uTime,uResolution,uImage;
  try{
    vertex=shader(gl.VERTEX_SHADER,'attribute vec2 a_position;varying vec2 v_uv;void main(){v_uv=(a_position+1.0)*0.5;gl_Position=vec4(a_position,0.0,1.0);}');
    fragment=shader(gl.FRAGMENT_SHADER,`precision mediump float;
      uniform sampler2D u_texture;uniform float u_time;uniform vec2 u_resolution;uniform vec2 u_image;varying vec2 v_uv;
      void main(){
        float viewAspect=u_resolution.x/u_resolution.y;float imageAspect=u_image.x/u_image.y;
        vec2 scale=viewAspect>imageAspect?vec2(1.0,imageAspect/viewAspect):vec2(viewAspect/imageAspect,1.0);
        vec2 uv=(v_uv-0.5)*scale+0.5;
        // Motion lives below the pearl sphere; keep the upper composition steady.
        float waveMask=1.0-smoothstep(0.30,0.62,uv.y);
        float edge=smoothstep(0.0,0.08,uv.x)*(1.0-smoothstep(0.92,1.0,uv.x))*smoothstep(0.0,0.08,uv.y);
        float t=u_time;
        float flow=sin(uv.x*10.0+t*0.65+uv.y*5.0)*0.009+sin(uv.x*19.0-uv.y*9.0-t*0.42)*0.004;
        uv.y+=flow*waveMask*edge;
        uv.x+=sin(uv.y*13.0+t*0.45)*0.005*waveMask*edge;
        gl_FragColor=texture2D(u_texture,clamp(uv,0.001,0.999));
      }`);
    program=gl.createProgram();gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error('Wave program unavailable');gl.useProgram(program);
    buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const position=gl.getAttribLocation(program,'a_position');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
    uTime=gl.getUniformLocation(program,'u_time');uResolution=gl.getUniformLocation(program,'u_resolution');uImage=gl.getUniformLocation(program,'u_image');
    texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.uniform1i(gl.getUniformLocation(program,'u_texture'),0);
  }catch(e){canvas.remove();if(program)gl.deleteProgram(program);if(texture)gl.deleteTexture(texture);if(buffer)gl.deleteBuffer(buffer);if(vertex)gl.deleteShader(vertex);if(fragment)gl.deleteShader(fragment);return ()=>{}}
  const image=new Image();image.decoding='async';
  function resize(){if(dead)return;const bounds=host.getBoundingClientRect();const dpr=Math.min(devicePixelRatio||1,compact?1:1.35);const cap=compact?850:1600;const ratio=Math.min(dpr,cap/Math.max(bounds.width,1));const w=Math.max(1,Math.round(bounds.width*ratio)),h=Math.max(1,Math.round(bounds.height*ratio));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h)}gl.uniform2f(uResolution,w,h);if(ready)draw()}
  function draw(){gl.uniform1f(uTime,elapsed);gl.drawArrays(gl.TRIANGLES,0,6)}
  function animate(now){frame=0;if(dead||!ready||!visible||document.hidden||preference.matches)return;if(!last)last=now;const delta=now-last;if(delta>=interval-1){elapsed+=Math.min(delta,70)/1000;last=now;draw()}frame=requestAnimationFrame(animate)}
  function sync(){cancelAnimationFrame(frame);frame=0;last=0;canvas.hidden=preference.matches;host.classList.toggle('wave-flow-ready',ready&&!preference.matches);if(!dead&&ready&&visible&&!document.hidden&&!preference.matches)frame=requestAnimationFrame(animate)}
  image.onload=()=>{if(dead)return;gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,image);gl.uniform2f(uImage,image.naturalWidth,image.naturalHeight);ready=true;resize();sync()};
  image.onerror=()=>{canvas.hidden=true;host.classList.remove('wave-flow-ready')};
  const cssURL=getComputedStyle(host).getPropertyValue('--silver-image-url').trim();
  const imageURL=cssURL.startsWith('url(')?cssURL.slice(4,-1).trim().replace(/^['"]|['"]$/g,''):cssURL;
  image.src=imageURL||'assets/silver-waves.jpg';
  const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync()},{rootMargin:'80px'});observer.observe(host);
  const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(host);
  const onLost=e=>{e.preventDefault();ready=false;host.classList.remove('wave-flow-ready');canvas.hidden=true;cancelAnimationFrame(frame)};canvas.addEventListener('webglcontextlost',onLost);
  document.addEventListener('visibilitychange',sync);preference.addEventListener('change',sync);
  return ()=>{dead=true;cancelAnimationFrame(frame);image.onload=null;image.onerror=null;observer.disconnect();resizeObserver.disconnect();document.removeEventListener('visibilitychange',sync);preference.removeEventListener('change',sync);canvas.removeEventListener('webglcontextlost',onLost);host.classList.remove('wave-flow-ready');canvas.remove();gl.deleteTexture(texture);gl.deleteBuffer(buffer);gl.deleteProgram(program);gl.deleteShader(vertex);gl.deleteShader(fragment)};
}
const silverStaticStart=startCinema;
startCinema=function(){silverStaticStart();const stopScroll=motionCleanup;const stopWaves=initSilverWaveFlow();motionCleanup=()=>{stopScroll();stopWaves()};};

;
