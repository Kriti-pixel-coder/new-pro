"use client";

import { useState, useEffect } from "react";
import CommandCenter, { Stage } from "./components/CommandCenter";
import PipelineTracker from "./components/PipelineTracker";
import TelemetryHub from "./components/TelemetryHub";
import ThreatGrid, { Vulnerability } from "./components/ThreatGrid";

const MOCK_VULNERABILITIES: Vulnerability[] = [
    { id: "1", file: "users/auth.py", line: 42, type: "SQL Injection", severity: "Critical", status: "Open" },
    { id: "2", file: "api/endpoints.py", line: 115, type: "Command Injection", severity: "High", status: "Open" },
    { id: "3", file: "utils/helpers.py", line: 23, type: "Insecure Deserialization", severity: "Critical", status: "Open" },
    { id: "4", file: "models/user.py", line: 88, type: "Hardcoded Credentials", severity: "High", status: "Open" },
    { id: "5", file: "ui/views.py", line: 201, type: "XSS", severity: "Medium", status: "Open" },
];

export default function Home() {
    const [stage, setStage] = useState<Stage>("Idle");
    const [progress, setProgress] = useState(0);
    const [logs, setLogs] = useState<string[]>([]);
    const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);

    const addLog = (msg: string) => setLogs(prev => [...prev, msg]);

    useEffect(() => {
        const source = new EventSource("http://localhost:8000/api/logs");

        source.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const msg = data.message;
            addLog(msg);

            // Basic inference from the text output to drive the UI stage
            if (msg.includes("ALL DONE") || msg.includes("SUCCESS:") || msg.includes("Pipeline Execution Finished")) {
                setStage("Secured");
                setProgress(100);
            } else if (msg.includes("Cloning repository")) {
                setStage("Cloning");
                setProgress(20);
            } else if (msg.includes("Found") || msg.includes("Semgrep") || msg.includes("vulnerabilities")) {
                setStage("Analyzing");
                setProgress(50);
            } else if (msg.includes("Starting") || msg.includes("HEALER") || msg.includes("Attempt") || msg.includes("patching")) {
                setStage("Healing");
                setProgress(75);
            }
        };

        // Poll for the actual bugs list from the backend
        const bugPoller = setInterval(async () => {
            try {
                const res = await fetch("http://localhost:8000/api/bugs");
                if (res.ok) {
                    const data = await res.json();

                    // Only update if we have new data and it's an array
                    setVulnerabilities(prev => {
                        return Array.isArray(data) ? data : [];
                    });
                }
            } catch (e) {
                // Silently fail if backend is restarting 
            }
        }, 2000);

        return () => {
            source.close();
            clearInterval(bugPoller);
        };
    }, []);

    const handleSecureClick = async (url: string) => {
        // Reset state
        setStage("Idle");
        setProgress(5);
        setLogs([]);
        setVulnerabilities([]);

        try {
            await fetch("http://localhost:8000/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_url: url })
            });
            setStage("Cloning");
        } catch (e) {
            addLog("❌ Error: Could not connect to Python backend at localhost:8000");
        }
    };
    const handleRetryClick = async () => {
        // Reset state for a new iteration without cloning
        setStage("Idle");
        setProgress(5);
        setLogs([]);
        setVulnerabilities([]);

        try {
            await fetch("http://localhost:8000/api/retry", {
                method: "POST"
            });
            setStage("Analyzing");
        } catch (e) {
            addLog("❌ Error: Could not connect to Python backend at localhost:8000");
        }
    };

    return (
        <main className="min-h-screen bg-[var(--color-rakshak-bg)] font-sans text-[var(--color-rakshak-text)] flex flex-col">
            <CommandCenter
                currentStage={stage}
                onSecureClick={handleSecureClick}
                onRetryClick={handleRetryClick}
                progress={progress}
                hasVulnerabilities={!!vulnerabilities && vulnerabilities.length > 0}
            />

            <div className="flex-1 flex flex-col max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8">
                <PipelineTracker currentStage={stage} />

                <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-8 pb-10 min-h-0">
                    {/* Left Column: Live Telemetry */}
                    <div className="h-[600px]">
                        <TelemetryHub logs={logs} />
                    </div>

                    {/* Right Column: Threat Grid */}
                    <div className="h-[600px]">
                        <ThreatGrid
                            vulnerabilities={((stage === "Idle" || stage === "Cloning") ? [] : vulnerabilities) || []}
                            currentStage={stage}
                        />
                    </div>
                </div>
            </div>
        </main>
    );
}
