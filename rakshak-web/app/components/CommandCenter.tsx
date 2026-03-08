"use client";

import { useState } from "react";
import { ShieldCheck, Search, ShieldAlert, Cpu, Download, RotateCcw } from "lucide-react";
import { cn } from "../lib/utils";
import { motion } from "framer-motion";

export const STAGES = ["Idle", "Cloning", "Analyzing", "Healing", "Secured"] as const;
export type Stage = typeof STAGES[number];

type Props = {
    currentStage: Stage;
    onSecureClick: (url: string) => void;
    onRetryClick?: () => void;
    progress: number;
    hasVulnerabilities: boolean;
};

export default function CommandCenter({ currentStage, onSecureClick, onRetryClick, progress, hasVulnerabilities }: Props) {
    const [url, setUrl] = useState("https://github.com/fportantier/vulpy.git");
    const isBusy = currentStage !== "Idle" && currentStage !== "Secured";

    return (
        <div className="w-full flex justify-between items-center py-6 px-10 border-b border-[var(--color-rakshak-border)] glass-panel sticky top-0 z-50">
            {/* Logo & Branding */}
            <div className="flex items-center space-x-3">
                <div className="bg-[var(--color-rakshak-text)] text-white p-2 rounded-md shadow-sm">
                    <ShieldAlert className="w-5 h-5" />
                </div>
                <div className="flex flex-col">
                    <h1 className="text-xl font-medium tracking-tight leading-none text-[var(--color-rakshak-text)]">RAKSHAK</h1>
                    <span className="text-xs text-gray-500 font-medium tracking-wider mt-1 uppercase">DevSecOps Guardian</span>
                </div>
            </div>

            {/* Input Hero Area */}
            <div className="flex-1 max-w-2xl mx-10">
                <div className={cn(
                    "flex items-center bg-white border border-[var(--color-rakshak-border)] overflow-hidden transition-all duration-300",
                    isBusy ? "opacity-70 grayscale h-12 rounded-full" : "h-14 rounded-md shadow-sm focus-within:ring-1 focus-within:ring-[var(--color-rakshak-text)]"
                )}>
                    <div className="pl-4 text-gray-400">
                        {isBusy ? <Cpu className="w-5 h-5 animate-pulse text-[var(--color-rakshak-text)]" /> : <Search className="w-5 h-5" />}
                    </div>
                    <input
                        type="text"
                        className="flex-1 h-full px-4 outline-none text-[var(--color-rakshak-text)] placeholder:text-gray-400 font-medium disabled:bg-white"
                        placeholder="Enter Public GitHub Repo URL..."
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        disabled={isBusy}
                    />
                    <button
                        onClick={() => onSecureClick(url)}
                        disabled={isBusy || !url}
                        className={cn(
                            "h-full px-8 flex items-center justify-center font-medium transition-colors border-l border-[var(--color-rakshak-border)]",
                            isBusy
                                ? "bg-gray-100 text-gray-500 cursor-not-allowed"
                                : "bg-[var(--color-rakshak-bg)] hover:bg-gray-100 text-[var(--color-rakshak-text)]"
                        )}
                    >
                        {isBusy ? "Processing..." : "Secure Repository"}
                    </button>
                </div>
            </div>

            {/* Security Score Gauge */}
            <div className="flex items-center space-x-4">
                {currentStage === "Secured" && onRetryClick && hasVulnerabilities && (
                    <button
                        onClick={onRetryClick}
                        className="mr-2 px-4 py-2 text-xs font-semibold bg-[var(--color-rakshak-text)] text-[var(--color-rakshak-bg)] rounded-md hover:bg-gray-800 transition-colors shadow-sm flex items-center gap-2"
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Rerun Once
                    </button>
                )}

                {currentStage === "Secured" && (
                    <a
                        href="http://localhost:8000/api/download"
                        download
                        className="mr-2 px-4 py-2 text-xs font-semibold bg-[var(--color-rakshak-success)] text-white rounded-md hover:opacity-90 transition-opacity shadow-sm flex items-center gap-2"
                    >
                        <Download className="w-3.5 h-3.5" />
                        Download Secured ZIP
                    </a>
                )}

                <div className="flex flex-col items-end">
                    <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Security Posture</span>
                    <span className="text-sm font-medium text-[var(--color-rakshak-text)]">
                        {currentStage === "Secured" ? "Optimal" : currentStage === "Idle" ? "Unknown" : "Scanning..."}
                    </span>
                </div>

                {/* SVG Circular Progress */}
                <div className="relative w-12 h-12">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                        <path
                            className="text-[var(--color-rakshak-border)]"
                            strokeDasharray="100, 100"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                        />
                        <motion.path
                            className={currentStage === "Secured" ? "text-[var(--color-rakshak-success)]" : "text-[var(--color-rakshak-text)]"}
                            strokeDasharray={`${progress}, 100`}
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                            initial={{ strokeDasharray: "0, 100" }}
                            animate={{ strokeDasharray: `${progress}, 100` }}
                            transition={{ duration: 1, ease: "easeInOut" }}
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        {currentStage === "Secured" ? (
                            <ShieldCheck className="w-4 h-4 text-[var(--color-rakshak-success)]" />
                        ) : (
                            <span className="text-xs font-semibold text-[var(--color-rakshak-text)]">{progress}%</span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
