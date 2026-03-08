"use client";

import { motion } from "framer-motion";
import { Bug, FileCode2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { cn } from "../lib/utils";
import { Stage } from "./CommandCenter";

export type Vulnerability = {
    id: string;
    file: string;
    line: number;
    type: string;
    severity: "Critical" | "High" | "Medium" | "Low";
    status: "Open" | "Fixing..." | "Secured" | "Unresolved";
};

type Props = {
    vulnerabilities: Vulnerability[];
    currentStage: Stage;
};

export default function ThreatGrid({ vulnerabilities, currentStage }: Props) {

    const vulns = vulnerabilities || [];

    if (vulns.length === 0 && currentStage === "Idle") {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-4">
                <Bug className="w-12 h-12 stroke-[1]" />
                <p className="text-sm">No active threats detected. Awaiting repository scan.</p>
            </div>
        );
    }

    if (vulns.length === 0 && currentStage === "Secured") {
        return (
            <div className="flex flex-col items-center justify-center h-full text-[var(--color-rakshak-success)] space-y-4">
                <CheckCircle2 className="w-12 h-12" />
                <p className="text-sm font-medium">All systems secure. Zero vulnerabilities found.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-transparent">
            <div className="flex items-center space-x-2 mb-4">
                <AlertTriangle className="w-4 h-4 text-[var(--color-rakshak-text)]" />
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-rakshak-text)]">Active Threats</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 auto-rows-max overflow-y-auto pb-8 terminal-scroll">
                {vulns.map((vuln, i) => (
                    <motion.div
                        key={vuln.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1, duration: 0.3 }}
                        whileHover={{ y: -4, transition: { duration: 0.2 } }}
                        className={cn(
                            "p-4 border border-[var(--color-rakshak-border)] rounded-md cursor-pointer transition-all duration-300 relative overflow-hidden group shadow-sm hover:shadow-md",
                            vuln.status === "Secured" ? "bg-green-50/50 opacity-60" :
                                vuln.status === "Unresolved" ? "bg-red-50/50 border-red-300" : "bg-white"
                        )}
                    >
                        {/* Status Indicator Bar */}
                        <div className={cn(
                            "absolute left-0 top-0 bottom-0 w-1",
                            vuln.status === "Secured" ? "bg-[var(--color-rakshak-success)]" :
                                vuln.status === "Unresolved" ? "bg-red-600" :
                                    vuln.severity === "Critical" ? "bg-[var(--color-rakshak-danger)]" :
                                        vuln.severity === "High" ? "bg-[var(--color-rakshak-warning)]" : "bg-[var(--color-rakshak-text)]"
                        )} />

                        <div className="flex flex-col space-y-3 pl-2">
                            <div className="flex items-start justify-between">
                                <span className={cn(
                                    "text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-sm",
                                    vuln.status === "Secured" ? "text-green-700 bg-green-100" :
                                        vuln.status === "Unresolved" ? "text-white bg-red-600 animate-pulse" :
                                            vuln.severity === "Critical" ? "text-red-700 bg-red-100" :
                                                vuln.severity === "High" ? "text-amber-700 bg-amber-100" : "text-gray-700 bg-gray-100"
                                )}>
                                    {vuln.status === "Secured" ? "RESOLVED" :
                                        vuln.status === "Unresolved" ? "UNRESOLVED - MANUAL FIX REQUIRED" :
                                            `${vuln.severity}: ${vuln.type}`}
                                </span>

                                {vuln.status === "Fixing..." && (
                                    <span className="flex h-2 w-2 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                                    </span>
                                )}
                            </div>

                            <div className="flex items-center space-x-2 text-sm font-medium text-[var(--color-rakshak-text)] group-hover:text-blue-600 transition-colors">
                                <FileCode2 className="w-4 h-4 text-gray-400" />
                                <span className="truncate">{vuln.file}</span>
                            </div>

                            {/* Subtle hover detail reveal */}
                            <div className="opacity-0 max-h-0 group-hover:opacity-100 group-hover:max-h-10 transition-all duration-300 ease-in-out font-mono text-[10px] text-gray-500 flex justify-between">
                                <span>Line: {vuln.line}</span>
                                <span>ID: {vuln.id.substring(0, 6)}</span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
