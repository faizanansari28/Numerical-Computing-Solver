import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

// Renders a LaTeX string. Use display for big centred formulas.
export default function Katex({ tex, display = false, className = "" }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(tex || "", { displayMode: display, throwOnError: false, strict: "ignore" });
    } catch {
      return tex;
    }
  }, [tex, display]);
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
