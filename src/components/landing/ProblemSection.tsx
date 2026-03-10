'use client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';
import { useScroll, useTransform, motion } from 'framer-motion';
import { useRef } from 'react';

const problems = [
    { title: 'Scattered Schemes', description: 'Benefits are spread across hundreds of confusing websites by Central & State Governments.' },
    { title: 'Complex Eligibility', description: 'Rules are hard to understand, leading to missed opportunities for millions of eligible citizens.' },
    { title: 'Lack of Guidance', description: 'No personalized help to navigate the application process and correct documents.' },
];

export function ProblemSection() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ['start start', 'end end']
    });

    return (
        <section ref={containerRef} className="relative bg-transparent h-[400vh]">
            <div className="sticky top-0 h-screen w-full flex flex-col items-center justify-center overflow-hidden">

                {/* Minimalist 3D Map of India (Background) */}
                <div className="absolute inset-0 z-0 flex items-center justify-center opacity-10 pointer-events-none">
                    <svg viewBox="0 0 600 600" className="w-[80vw] max-w-[800px] h-auto text-blue-500/30 animate-pulse">
                        <path fill="currentColor" d="M295.4,32.3c2.7-1.3,6.2-1.3,8.8,0l26.1,13.1c1.9,1,4.4,0.7,6-0.8l16.1-15c4.1-3.8,10.6-2.5,13,2.6l9.6,20.4 c1.2,2.5,4.3,3.7,6.9,2.7l23.5-9.1c3.2-1.2,6.7,0.5,7.7,3.8l5.2,16.8c0.7,2.2,2.8,3.7,5.1,3.7l20.4-0.1c2.8,0,5.3,1.8,6.2,4.5l6,18.1 c1.1,3.3,4.4,5.4,7.8,4.9l22.4-3.1c5-0.7,9.3,3.4,8.5,8.4l-1.9,11.8c-0.4,2.6,1,5.2,3.4,6.3l17.4,8.1c3.7,1.7,5.4,6.2,3.7,9.9 l-8.9,19.3c-1.2,2.6-0.4,5.7,1.9,7.5l21.2,16.6c2.8,2.2,3.6,6.2,1.8,9.3l-10.8,18.8c-1.3,2.3-1.1,5.2,0.6,7.3l15.6,19.5 c2.5,3.1,1.9,7.7-1.4,10.1l-14.8,10.7c-2.3,1.7-3.4,4.7-2.6,7.5l5.9,20.1c1,3.4-1.3,6.9-4.8,7.3l-18.3,2.1c-2.7,0.3-4.8,2.3-5.3,5 l-3.1,15.7c-0.7,3.5-4.4,5.4-7.7,4.1l-13.4-5.3c-2.8-1.1-6-0.1-7.8,2.4l-12.1,16.8c-2,2.8-5.8,3.5-8.8,1.6l-18.2-11.5 c-2.4-1.5-5.5-1.3-7.7,0.5l-19.1,15.6c-2.2,1.8-5.3,2.2-7.9,0.9l-22.1-10.9c-2.2-1.1-4.8-1.1-7,0l-20.1,10.1 c-2.4,1.2-5.3,1.1-7.6-0.3l-18.5-11.2c-3.1-1.9-7-1.1-9.2,1.8l-14.1,18.5c-1.9,2.5-1.9,6,0,8.5l14.1,18.5c2.2,2.9,1.4,6.8-1.7,8.7 l-18.5,11.2c-2.3,1.4-5.2,1.5-7.6,0.3L273,431c-2.2-1.1-4.8-1.1-7,0l-22.1,10.9c-2.6,1.3-5.7,0.9-7.9-0.9l-19.1-15.6 c-2.2-1.8-5.3-2-7.7-0.5l-18.2,11.5c-3,1.9-6.8,1.2-8.8-1.6l-12.1-16.8c-1.8-2.5-5-3.5-7.8-2.4l-13.4,5.3c-3.3,1.3-7-0.6-7.7-4.1 l-3.1-15.7c-0.5-2.7-2.6-4.7-5.3-5l-18.3-2.1c-3.5-0.4-5.8-3.9-4.8-7.3l5.9-20.1c0.8-2.8-0.3-5.8-2.6-7.5l-14.8-10.7 c-3.3-2.4-3.9-7-1.4-10.1l15.6-19.5c1.7-2.1,1.9-5,0.6-7.3l-10.8-18.8c-1.8-3.1-1-7.1,1.8-9.3l21.2-16.6c2.3-1.8,3.1-4.9,1.9-7.5 l-8.9-19.3c-1.7-3.7,0-8.2,3.7-9.9l17.4-8.1c2.4-1.1,3.8-3.7,3.4-6.3l-1.9-11.8c-0.8-5,3.5-9.1,8.5-8.4l22.4,3.1 c3.4,0.5,6.7-1.6,7.8-4.9l6-18.1c0.9-2.7,3.4-4.5,6.2-4.5l20.4,0.1c2.3,0,4.4-1.5,5.1-3.7l5.2-16.8c1-3.3,4.5-5,7.7-3.8l23.5,9.1 c2.6,1,5.7-0.2,6.9-2.7l9.6-20.4c2.4-5.1,8.9-6.4,13-2.6l16.1,15C291,31.6,293.5,31.9,295.4,32.3z" />
                    </svg>
                </div>

                <div className="absolute top-16 md:top-24 text-center max-w-3xl mx-auto px-4 z-10 hidden sm:block">
                    <h2 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight drop-shadow-md">
                        The Challenge for Citizens
                    </h2>
                    <p className="mt-4 text-xl text-slate-300 font-medium">
                        Millions miss out on government benefits they are entitled to.
                    </p>
                </div>

                <div className="relative w-full max-w-3xl h-full sm:h-[500px] flex justify-center items-center z-10 mt-10 md:mt-24">
                    {problems.map((problem, i) => {
                        // Better calculation for Stacking cards
                        // Each card becomes visible sequentially and moves UP into place
                        const start = i * 0.2;
                        const fullyVisible = start + 0.15;
                        const end = 1;

                        // Opacity: Appears slowly, stays fully visible
                        const opacity = useTransform(scrollYProgress, [start, fullyVisible], [0, 1]);

                        // Position Y: Starts low, moves up to 0, then slightly further up as others stack on
                        const y = useTransform(scrollYProgress, [start, fullyVisible, end], [300, 0, (problems.length - i) * -15]);

                        // Scale: Starts normal, scales down slightly when pushed back
                        const scale = useTransform(scrollYProgress, [fullyVisible, end], [1, 1 - (problems.length - 1 - i) * 0.04]);

                        return (
                            <motion.div
                                key={i}
                                style={{
                                    opacity,
                                    y,
                                    scale,
                                    zIndex: i,
                                    position: 'absolute',
                                    top: `${i * 20}px` // Initial vertical gap
                                }}
                                className="w-[90%] sm:w-full"
                            >
                                <Card className="bg-[#050510] shadow-[0_-10px_30px_rgba(0,0,0,0.5)] border border-slate-700/50 rounded-3xl p-6 sm:p-8 md:h-[220px] flex flex-col justify-center relative overflow-hidden group">
                                    <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
                                    <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-transparent to-transparent opacity-50" />

                                    <CardHeader className="pb-3 relative z-10 px-0">
                                        <CardTitle className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-4">
                                            <div className="w-10 h-10 shrink-0 rounded-full bg-blue-500/20 border border-blue-400/50 flex items-center justify-center text-blue-300 font-black">
                                                {i + 1}
                                            </div>
                                            {problem.title}
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="relative z-10 px-0 sm:pl-14">
                                        <p className="text-slate-300 text-lg leading-relaxed">{problem.description}</p>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        );
                    })}

                    {/* Final AI Solution Card */}
                    <motion.div
                        style={{
                            opacity: useTransform(scrollYProgress, [0.75, 0.85], [0, 1]),
                            y: useTransform(scrollYProgress, [0.75, 0.85], [400, problems.length * 20 + 20]),
                            scale: useTransform(scrollYProgress, [0.8, 0.9], [0.95, 1.05]),
                            zIndex: 10,
                            position: 'absolute'
                        }}
                        className="w-[95%] sm:w-[105%]"
                    >
                        <Card className="p-8 sm:p-10 bg-gradient-to-br from-blue-950/80 to-[#020205] border border-blue-400/50 shadow-[0_-20px_50px_rgba(0,0,0,0.8)] backdrop-blur-3xl rounded-[2.5rem] relative overflow-hidden">
                            {/* Tricolor Glow representing solution */}
                            <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-[#ea580c] via-[#ffffff] to-[#10b981]" />
                            <div className="absolute -inset-10 bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-3xl rounded-full opacity-50 pointer-events-none" />

                            <div className="flex flex-col md:flex-row items-center justify-center gap-8 text-center md:text-left relative z-10">
                                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white p-6 rounded-2xl flex-shrink-0 shadow-[0_0_30px_rgba(99,102,241,0.5)] rotate-3">
                                    <Lightbulb className="w-10 h-10" />
                                </div>
                                <div>
                                    <h3 className="text-3xl sm:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-white tracking-tight">
                                        The AI Solution
                                    </h3>
                                    <p className="text-slate-300 mt-3 text-lg font-medium leading-relaxed">
                                        CivixAI uses artificial intelligence to instantly cut through the noise, matching you to the right schemes accurately.
                                    </p>
                                </div>
                            </div>
                        </Card>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
