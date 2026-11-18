import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Cursor from "./components/Cursor";
import Home from "./pages/Home";
import Learn from "./pages/Learn";
import MethodDetail from "./pages/MethodDetail";
import Solver from "./pages/Solver";
import Challenge from "./pages/Challenge";

function Shell({ children, footer = true }) {
  return (
    <motion.main initial={{ opacity: 0, y: 18, filter: "blur(6px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} exit={{ opacity: 0, y: -10, filter: "blur(4px)" }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
      {children}
      {footer && <Footer />}
    </motion.main>
  );
}

export default function App() {
  const location = useLocation();
  useEffect(() => {
    if (location.hash) {
      const t = setTimeout(() => document.querySelector(location.hash)?.scrollIntoView({ behavior: "smooth" }), 350);
      return () => clearTimeout(t);
    }
    window.scrollTo(0, 0);
  }, [location.pathname, location.hash]);

  return (
    <>
      <Cursor />
      <Navbar />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Shell><Home /></Shell>} />
          <Route path="/methods" element={<Shell footer={false}><Learn /></Shell>} />
          <Route path="/methods/:id" element={<Shell><MethodDetail /></Shell>} />
          <Route path="/calculator" element={<Shell><Solver /></Shell>} />
          <Route path="/challenge" element={<Shell><Challenge /></Shell>} />
          <Route path="*" element={<Shell><Home /></Shell>} />
        </Routes>
      </AnimatePresence>
    </>
  );
}
