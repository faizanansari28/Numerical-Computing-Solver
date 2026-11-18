import { useEffect, useRef } from "react";

// Small glowing cursor for mouse users (hidden on touch devices).
export default function Cursor() {
  const dot = useRef(null);
  const ring = useRef(null);
  useEffect(() => {
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    document.body.classList.add("has-cursor");
    let x = -100, y = -100, rx = -100, ry = -100, raf;
    const move = (e) => {
      x = e.clientX; y = e.clientY;
      const hot = e.target.closest && e.target.closest("a, button, .hot, input, select, textarea, [role=button]");
      ring.current?.classList.toggle("hot", !!hot);
    };
    const loop = () => {
      rx += (x - rx) * 0.18; ry += (y - ry) * 0.18;
      if (dot.current) dot.current.style.transform = `translate(${x}px, ${y}px)`;
      if (ring.current) ring.current.style.transform = `translate(${rx}px, ${ry}px)`;
      raf = requestAnimationFrame(loop);
    };
    window.addEventListener("mousemove", move);
    raf = requestAnimationFrame(loop);
    return () => { window.removeEventListener("mousemove", move); cancelAnimationFrame(raf); document.body.classList.remove("has-cursor"); };
  }, []);
  return (<><div ref={ring} className="cursor-ring" /><div ref={dot} className="cursor-dot" /></>);
}
