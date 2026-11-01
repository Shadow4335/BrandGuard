"use client";

import { useEffect, useRef } from "react";

/** Adapted from the supplied renderer: static JPEG fallback, bounded GPU work, full cleanup. */
export function SilverWaves({ className = "", children }: { className?: string; children?: React.ReactNode }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    const preference = matchMedia("(prefers-reduced-motion: reduce)");
    let stop = () => {};
    function start() {
      stop();
      if (preference.matches || document.documentElement.dataset.reduceMotion || !el) return;
      const canvas = document.createElement("canvas");
      canvas.className = "silver-wave-canvas"; canvas.setAttribute("aria-hidden", "true");
      const gl = canvas.getContext("webgl", { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: "low-power" });
      if (!gl) return;
      let dead = false, ready = false, visible = false, frame = 0, last = 0, elapsed = 0;
      const shaders: WebGLShader[] = [];
      let program: WebGLProgram | null = null, texture: WebGLTexture | null = null, buffer: WebGLBuffer | null = null;
      const dispose = () => { gl.deleteTexture(texture); gl.deleteBuffer(buffer); gl.deleteProgram(program); shaders.forEach((s) => gl.deleteShader(s)); };
      try {
        function shader(type: number, source: string) {
          const s = gl!.createShader(type); if (!s) throw Error("shader"); shaders.push(s);
          gl!.shaderSource(s, source); gl!.compileShader(s);
          if (!gl!.getShaderParameter(s, gl!.COMPILE_STATUS)) throw Error("shader");
          return s;
        }
        const vertex = shader(gl.VERTEX_SHADER, "attribute vec2 a_position;varying vec2 v_uv;void main(){v_uv=(a_position+1.0)*0.5;gl_Position=vec4(a_position,0.0,1.0);}");
        const fragment = shader(gl.FRAGMENT_SHADER, `precision mediump float;
          uniform sampler2D u_texture;uniform float u_time;uniform vec2 u_resolution;uniform vec2 u_image;uniform vec2 u_crop;varying vec2 v_uv;
          void main(){float va=u_resolution.x/u_resolution.y;float ia=u_image.x/u_image.y;
          vec2 scale=va>ia?vec2(1.0,ia/va):vec2(va/ia,1.0);vec2 uv=v_uv*scale+u_crop*(1.0-scale);
          float mask=1.0-smoothstep(0.30,0.62,uv.y);float edge=smoothstep(0.0,0.08,uv.x)*(1.0-smoothstep(0.92,1.0,uv.x))*smoothstep(0.0,0.08,uv.y);
          uv.y+=(sin(uv.x*10.0+u_time*0.65+uv.y*5.0)*0.009+sin(uv.x*19.0-uv.y*9.0-u_time*0.42)*0.004)*mask*edge;
          uv.x+=sin(uv.y*13.0+u_time*0.45)*0.005*mask*edge;gl_FragColor=texture2D(u_texture,clamp(uv,0.001,0.999));}`);
        program = gl.createProgram(); if (!program) throw Error("program");
        gl.attachShader(program, vertex); gl.attachShader(program, fragment); gl.linkProgram(program);
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error("link");
        gl.useProgram(program); buffer = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
        const position = gl.getAttribLocation(program, "a_position"); gl.enableVertexAttribArray(position); gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
        texture = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.uniform1i(gl.getUniformLocation(program, "u_texture"), 0);
      } catch { dispose(); return; }
      el.appendChild(canvas);
      const time = gl.getUniformLocation(program!, "u_time"), resolution = gl.getUniformLocation(program!, "u_resolution"), imageSize = gl.getUniformLocation(program!, "u_image"), crop = gl.getUniformLocation(program!, "u_crop");
      function draw() { gl!.uniform1f(time, elapsed); gl!.drawArrays(gl!.TRIANGLES, 0, 6); }
      function resize() {
        if (dead) return;
        const b = el!.getBoundingClientRect(), mobile = b.width < 760;
        const ratio = Math.min(devicePixelRatio || 1, mobile ? 1 : 1.35, (mobile ? 850 : 1600) / Math.max(b.width, 1));
        canvas.width = Math.max(1, Math.round(b.width * ratio)); canvas.height = Math.max(1, Math.round(b.height * ratio));
        gl!.viewport(0, 0, canvas.width, canvas.height); gl!.uniform2f(resolution, canvas.width, canvas.height); gl!.uniform2f(crop, mobile ? .61 : .5, mobile ? .6 : .58);
        if (ready) draw();
      }
      function animate(now: number) {
        frame = 0; if (dead || !ready || !visible || document.hidden) return;
        if (!last) last = now;
        const delta = now - last;
        if (delta >= 1000 / (el!.clientWidth < 760 ? 30 : 60) - 1) { elapsed += Math.min(delta, 70) / 1000; last = now; draw(); }
        frame = requestAnimationFrame(animate);
      }
      function sync() { cancelAnimationFrame(frame); last = 0; if (!dead && ready && visible && !document.hidden) frame = requestAnimationFrame(animate); }
      const image = new Image(); image.decoding = "async";
      image.onload = () => { if (dead) return; gl!.bindTexture(gl!.TEXTURE_2D, texture); gl!.pixelStorei(gl!.UNPACK_FLIP_Y_WEBGL, true); gl!.texImage2D(gl!.TEXTURE_2D, 0, gl!.RGB, gl!.RGB, gl!.UNSIGNED_BYTE, image); gl!.uniform2f(imageSize, image.naturalWidth, image.naturalHeight); ready = true; resize(); canvas.classList.add("ready"); sync(); };
      image.src = "/brand/silver-waves.jpg";
      const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); }); observer.observe(el);
      const ro = new ResizeObserver(resize); ro.observe(el);
      const lost = (e: Event) => { e.preventDefault(); ready = false; canvas.classList.remove("ready"); cancelAnimationFrame(frame); };
      canvas.addEventListener("webglcontextlost", lost); document.addEventListener("visibilitychange", sync);
      stop = () => { dead = true; cancelAnimationFrame(frame); image.onload = null; image.onerror = null; observer.disconnect(); ro.disconnect(); document.removeEventListener("visibilitychange", sync); canvas.removeEventListener("webglcontextlost", lost); canvas.remove(); dispose(); };
    }
    start(); preference.addEventListener("change", start);
    const mo = new MutationObserver(start); mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-reduce-motion"] });
    return () => { stop(); mo.disconnect(); preference.removeEventListener("change", start); };
  }, []);
  return <div ref={host} className={`silver-waves ${className}`}>{children}</div>;
}
