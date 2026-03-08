"use client";

import { useEffect, useRef } from "react";
import { Terminal, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Props = {
    logs: string[];
};

export default function TelemetryHub({ logs }: Props) {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of terminal
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="flex flex-col h-full bg-white border border-[var(--color-rakshak-border)] shadow-sm rounded-md overflow-hidden relative">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-rakshak-border)] bg-[var(--color-rakshak-bg)]">
                <div className="flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-gray-500" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Live Telemetry</span>
                </div>
                <div className="flex items-center space-x-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-rakshak-success)] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-rakshak-success)]"></span>
                    </span>
                    <span className="text-[10px] text-gray-400 font-medium">CONNECTED</span>
                </div>
            </div>

            {/* Logs Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-2 terminal-scroll font-mono text-xs text-[var(--color-rakshak-text)] leading-relaxed"
            >
                <AnimatePresence initial={false}>
                    {(logs || []).map((log, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.2 }}
                            className="flex items-start"
                        >
                            <span className="text-gray-400 mr-3 shrink-0">
                                [{new Date().toLocaleTimeString('en-US', { hour12: false, hour: "numeric", minute: "numeric", second: "numeric" })}]
                            </span>
                            <span className="break-all">{log}</span>
                        </motion.div>
                    ))}
                    {(logs || []).length === 0 && (
                        <div className="text-gray-400 italic">Waiting for pipeline execution...</div>
                    )}
                </AnimatePresence>
            </div>

            {/* Gradient overlay to fade bottom slightly */}
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-white to-transparent pointer-events-none" />
        </div>
    );
}
