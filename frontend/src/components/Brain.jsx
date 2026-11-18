import { useMemo, useRef, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

/* ------------------------------------------------------------------
   A brain made of thousands of particles.
   1. buildBrain() places points inside / on the surface of several
      ellipsoids (two hemispheres, temporal lobes, cerebellum) plus a
      tube for the brainstem, with "folds" added by sine noise.
   2. A GLSL vertex shader scatters the points (dissolve) and pushes them
      away from the mouse, a fragment shader draws soft glowing dots.
------------------------------------------------------------------- */
function mulberry32(a) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const smooth = (a, b, x) => { const t = Math.min(Math.max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); };
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);

function buildBrain(count) {
  const rnd = mulberry32(20241);
  const dir = () => { const u = rnd() * 2 - 1, t = rnd() * Math.PI * 2, s = Math.sqrt(1 - u * u); return [s * Math.cos(t), u, s * Math.sin(t)]; };
  const fold = (dx, dy, dz) => Math.sin(dx * 9 + dz * 6) * Math.sin(dy * 8 + dz * 4) + 0.6 * Math.sin(dz * 15 + dx * 4 + dy * 3);
  const shell = () => 1 - 0.2 * Math.pow(rnd(), 1.6);

  const hemisphere = (side) => {
    const [dx, dy, dz] = dir();
    const rr = shell() * (1 + 0.055 * fold(dx, dy, dz));
    let x = side * 0.64 + dx * 0.7 * rr, y = 0.12 + dy * 0.95 * rr, z = 0.05 + dz * 1.55 * rr;
    x = side * Math.max(Math.abs(x), 0.07 + 0.03 * Math.abs(Math.sin(z * 6)));       // longitudinal fissure
    if (y < -0.2) y = -0.2 + (y + 0.2) * 0.5;                                          // flat underside
    y += z * 0.07;
    return [x, y, z];
  };
  const temporal = (side) => {
    const [dx, dy, dz] = dir();
    const rr = shell() * (1 + 0.05 * fold(dx, dy, dz));
    return [side * (0.82 + dx * 0.34 * rr), -0.5 + dy * 0.26 * rr, 0.3 + dz * 0.66 * rr];
  };
  const cerebellum = () => {
    const [dx, dy, dz] = dir();
    const rr = shell() * (1 + 0.05 * Math.sin(30 * dy + 3 * dx));
    return [dx * 0.8 * rr, -0.66 + dy * 0.34 * rr, -1.12 + dz * 0.5 * rr];
  };
  const stem = () => {
    const t = rnd(), phi = rnd() * Math.PI * 2, rad = (0.22 - 0.06 * t) * (0.55 + 0.45 * Math.sqrt(rnd()));
    return [rad * Math.cos(phi), -0.45 - 1.3 * t, -0.52 - 0.35 * t + rad * Math.sin(phi)];
  };

  const positions = new Float32Array(count * 3), colors = new Float32Array(count * 3), randoms = new Float32Array(count * 3), seeds = new Float32Array(count);
  const PURPLE = [0.5, 0.33, 1.0], BLUE = [0.38, 0.48, 1.0], GREY = [0.84, 0.84, 0.93], GOLD = [0.96, 0.72, 0.36];
  for (let i = 0; i < count; i++) {
    const r = rnd();
    let p;
    if (r < 0.31) p = hemisphere(1);
    else if (r < 0.62) p = hemisphere(-1);
    else if (r < 0.71) p = temporal(r < 0.665 ? 1 : -1);
    else if (r < 0.88) p = cerebellum();
    else if (r < 0.96) p = stem();
    else p = hemisphere(rnd() < 0.5 ? 1 : -1);
    p[1] += 0.28;
    positions.set(p, i * 3);
    const h = (p[1] + 1.5) / 2.6;
    const wt = smooth(0.52, 0.82, h), wl = 1 - smooth(0.12, 0.4, h);
    let c = GREY.slice();
    c = mix(c, mix(PURPLE, BLUE, rnd()), wt);
    c = mix(c, mix(GOLD, PURPLE, 0.2 + 0.4 * rnd()), wl);
    const v = 0.85 + rnd() * 0.3;
    colors.set([c[0] * v, c[1] * v, c[2] * v], i * 3);
    randoms.set([rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1], i * 3);
    seeds[i] = rnd();
  }
  return { positions, colors, randoms, seeds };
}

const vertex = /* glsl */ `
  attribute vec3 aColor; attribute vec3 aRand; attribute float aSeed;
  uniform float uTime, uDissolve, uPx, uSize, uOpacity, uAspect;
  uniform vec2 uMouse;
  varying vec3 vColor; varying float vGlow, vAlpha;
  void main() {
    vec3 p = position;
    float t = clamp(uDissolve * 1.5 - aSeed * 0.5, 0.0, 1.0);
    t = t * t * (3.0 - 2.0 * t);
    vec3 drift = vec3(sin(uTime * 0.5 + aSeed * 20.0), cos(uTime * 0.4 + aSeed * 14.0), sin(uTime * 0.3 + aSeed * 9.0)) * 0.3;
    vec3 target = p + normalize(aRand + 0.001) * (1.5 + 2.6 * aSeed) + drift;
    p = mix(p, target, t);
    p += normalize(p + 0.001) * 0.012 * sin(uTime * 1.3 + aSeed * 40.0);
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    vec4 clip = projectionMatrix * mv;
    vec2 d = (clip.xy / clip.w - uMouse) * vec2(uAspect, 1.0);
    float dist = length(d);
    float infl = smoothstep(0.34, 0.0, dist);
    float ripple = 0.65 + 0.35 * sin(dist * 42.0 - uTime * 7.0);
    mv.xy += normalize(d + 1e-5) * infl * ripple * 0.6;
    mv.z += infl * 0.6;
    vGlow = infl; vColor = aColor; vAlpha = mix(1.0, 0.5, t) * uOpacity;
    gl_Position = projectionMatrix * mv;
    gl_PointSize = uSize * (1.0 + infl * 1.8) * uPx * (6.0 / -mv.z);
  }`;
const fragment = /* glsl */ `
  varying vec3 vColor; varying float vGlow, vAlpha;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;
    float a = smoothstep(0.5, 0.0, d);
    vec3 col = mix(vColor, vec3(1.0), vGlow * 0.65);
    gl_FragColor = vec4(col, a * vAlpha * (0.62 + vGlow * 0.7));
  }`;

function Particles({ progress, count }) {
  const group = useRef(), mat = useRef();
  const mouse = useRef({ x: 9, y: 9, sx: 9, sy: 9, rx: 0, ry: 0 });
  const { size, viewport } = useThree();
  const data = useMemo(() => buildBrain(count), [count]);
  const uniforms = useMemo(() => ({
    uTime: { value: 0 }, uDissolve: { value: 0 }, uPx: { value: 1 }, uSize: { value: 2.4 }, uOpacity: { value: 1 },
    uAspect: { value: 1 }, uMouse: { value: new THREE.Vector2(9, 9) },
  }), []);

  useEffect(() => {
    const move = (e) => {
      const p = e.touches ? e.touches[0] : e;
      mouse.current.x = (p.clientX / window.innerWidth) * 2 - 1;
      mouse.current.y = -(p.clientY / window.innerHeight) * 2 + 1;
    };
    const leave = () => { mouse.current.x = 9; mouse.current.y = 9; };
    window.addEventListener("pointermove", move);
    window.addEventListener("touchmove", move, { passive: true });
    window.addEventListener("pointerleave", leave);
    document.addEventListener("mouseleave", leave);
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("touchmove", move); window.removeEventListener("pointerleave", leave); document.removeEventListener("mouseleave", leave); };
  }, []);

  const state = useRef({ p: 0, dissolve: 0 });
  useFrame((st, dt) => {
    const m = mouse.current, s = state.current;
    const k = 1 - Math.pow(0.0015, dt);
    s.p += (progress.current - s.p) * k * 0.9;                      // smoothed scroll progress
    const p = s.p;
    const portrait = size.width / size.height < 0.95;
    const halfW = viewport.width / 2;
    const toCenter = smooth(0, 1, p);
    const rightX = portrait ? 0 : halfW * 0.40;
    const baseY = portrait ? viewport.height * 0.16 : 0;
    const baseScale = portrait ? Math.min(1.05, viewport.width / 3.0) : Math.min(1.12, viewport.height / 4.0);
    const g = group.current;
    g.position.x += ((rightX * (1 - toCenter)) - g.position.x) * 0.12;
    g.position.y += ((baseY * (1 - toCenter * 0.6)) - g.position.y) * 0.12;
    const sc = baseScale * (1 - 0.18 * toCenter);
    g.scale.setScalar(g.scale.x + (sc - g.scale.x) * 0.12);
    const dis = p < 2 ? smooth(1, 2, p) : 1 - smooth(2, 3, p);
    mat.current.uniforms.uDissolve.value = dis;
    m.rx += ((m.x < 5 ? m.x : 0) * 0.35 - m.rx) * 0.05; m.ry += ((m.y < 5 ? m.y : 0) * 0.18 - m.ry) * 0.05;
    g.rotation.y = -1.0 + st.clock.elapsedTime * 0.11 + m.rx;
    g.rotation.x = -0.05 - m.ry;
    m.sx += (m.x - m.sx) * 0.25; m.sy += (m.y - m.sy) * 0.25;
    const u = mat.current.uniforms;
    u.uMouse.value.set(m.sx, m.sy);
    u.uTime.value = st.clock.elapsedTime;
    u.uPx.value = st.gl.getPixelRatio();
    u.uAspect.value = size.width / size.height;
  });

  return (
    <group ref={group}>
      <points frustumCulled={false}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" array={data.positions} count={count} itemSize={3} />
          <bufferAttribute attach="attributes-aColor" array={data.colors} count={count} itemSize={3} />
          <bufferAttribute attach="attributes-aRand" array={data.randoms} count={count} itemSize={3} />
          <bufferAttribute attach="attributes-aSeed" array={data.seeds} count={count} itemSize={1} />
        </bufferGeometry>
        <shaderMaterial ref={mat} vertexShader={vertex} fragmentShader={fragment} uniforms={uniforms} transparent depthWrite={false} blending={THREE.AdditiveBlending} />
      </points>
    </group>
  );
}

export default function Brain({ progress }) {
  const count = typeof window !== "undefined" && window.innerWidth < 700 ? 15000 : 28000;
  return (
    <Canvas camera={{ position: [0, 0, 6], fov: 45 }} dpr={[1, 1.6]} gl={{ antialias: false, alpha: true, powerPreference: "high-performance" }} style={{ position: "absolute", inset: 0 }}>
      <Particles progress={progress} count={count} />
    </Canvas>
  );
}
