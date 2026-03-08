"use client";

import { Check, Dot } from "lucide-react";
import { STAGES, Stage } from "./CommandCenter";
import { cn } from "../lib/utils";
import { motion } from "framer-motion";

type Props = {
    currentStage: Stage;
};

export default function PipelineTracker({ currentStage }: Props) {
    const steps = STAGES.filter(s => s !== "Idle");
    const currentIndex = steps.indexOf(currentStage === "Idle" ? "Cloning" : currentStage);

    return (
        <div className="w-full py-8 px-10">
            <div className="flex items-center justify-between relative max-w-4xl mx-auto">

                {/* Background Line */}
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-[1px] bg-[var(--color-rakshak-border)] z-0" />

                {/* Progress Line */}
                <motion.div
                    className="absolute left-0 top-1/2 -translate-y-1/2 h-[2px] bg-[var(--color-rakshak-text)] z-0"
                    initial={{ width: "0%" }}
                    animate={{
                        width: currentStage === "Idle" ? "0%" : `${(currentIndex / (steps.length - 1)) * 100}%`
                    }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                />

                {steps.map((step, index) => {
                    // Define states: completed, active, upcoming
                    const isCompleted = currentStage !== "Idle" && index < currentIndex;
                    const isActive = currentStage !== "Idle" && index === currentIndex;
                    const isUpcoming = currentStage === "Idle" || index > currentIndex;

                    return (
                        <div key={step} className="flex flex-col items-center relative z-10 space-y-3">
                            <motion.div
                                initial={false}
                                animate={{
                                    scale: isActive ? 1.2 : 1,
                                    backgroundColor: isCompleted || isActive ? "var(--color-rakshak-text)" : "#FFFFFF",
                                    borderColor: isCompleted || isActive ? "var(--color-rakshak-text)" : "var(--color-rakshak-border)",
                                    color: isCompleted || isActive ? "#FFFFFF" : "var(--color-rakshak-border)"
                                }}
                                className={cn(
                                    "w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-sm bg-white transition-colors duration-300",
                                )}
                            >
                                {isCompleted ? (
                                    <Check className="w-4 h-4 text-white" />
                                ) : isActive ? (
                                    <span className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                                ) : (
                                    <span className="w-2.5 h-2.5 rounded-full bg-gray-200" />
                                )}
                            </motion.div>

                            <span className={cn(
                                "text-xs font-semibold uppercase tracking-wider transition-colors duration-300",
                                isActive ? "text-[var(--color-rakshak-text)]" : "text-gray-400"
                            )}>
                                {step}
                            </span>
                        </div>
                    );
                })}

            </div>
        </div>
    );
}
