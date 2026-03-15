"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeftRight } from "lucide-react";

interface SwapButtonProps {
  onSwap: () => void;
}

export function SwapButton({ onSwap }: SwapButtonProps) {
  const [rotation, setRotation] = useState(0);

  return (
    <motion.button
      onClick={() => { setRotation((r) => r + 180); onSwap(); }}
      animate={{ rotate: rotation }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="flex size-8 items-center justify-center rounded-full border border-[hsla(0,0%,100%,.12)] bg-[#0a0a0a] text-[hsla(0,0%,100%,.35)] shadow-sm transition-colors hover:border-emerald-500/30 hover:text-emerald-400"
      aria-label="Swap origin and destination"
    >
      <ArrowLeftRight className="size-[14px]" />
    </motion.button>
  );
}
