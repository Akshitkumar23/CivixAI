'use client';

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function NetworkNodes() {
    const groupRef = useRef<THREE.Group>(null!);
    const count = 300;
    const maxDistance = 3.5;

    // Generate positions and lines securely
    const { positions, colors, linePositions, lineColors } = useMemo(() => {
        const points = [];
        const colorsArr = [];

        // Colors for Government Theme (Saffron, White, Green, Trustworthy Blue)
        const themeColors = [
            new THREE.Color('#ea580c'), // Saffron-ish
            new THREE.Color('#10b981'), // Green
            new THREE.Color('#3b82f6'), // Trust Blue
            new THREE.Color('#ffffff'), // White
            new THREE.Color('#60a5fa'), // Light Blue
        ];

        // 1. Generate random nodes within a rectangular space
        for (let i = 0; i < count; i++) {
            const x = (Math.random() - 0.5) * 35;
            const y = (Math.random() - 0.5) * 20;
            const z = (Math.random() - 0.5) * 15;
            points.push(new THREE.Vector3(x, y, z));

            const color = themeColors[Math.floor(Math.random() * themeColors.length)];
            colorsArr.push(color.r, color.g, color.b);
        }

        const lines = [];
        const linesCols = [];

        // 2. Connect nodes that are close to each other
        for (let i = 0; i < count; i++) {
            for (let j = i + 1; j < count; j++) {
                const dist = points[i].distanceTo(points[j]);
                if (dist < maxDistance) {
                    lines.push(
                        points[i].x, points[i].y, points[i].z,
                        points[j].x, points[j].y, points[j].z
                    );

                    // Mix color for lines based on points distance/opacity logic
                    // Here we just use a subtle semi-transparent blue/white
                    linesCols.push(
                        0.2, 0.4, 0.8, // subtle blueish
                        0.2, 0.4, 0.8
                    );
                }
            }
        }

        const positions = new Float32Array(count * 3);
        const ptsColors = new Float32Array(colorsArr);
        points.forEach((p, i) => {
            positions[i * 3] = p.x;
            positions[i * 3 + 1] = p.y;
            positions[i * 3 + 2] = p.z;
        });

        const linePositions = new Float32Array(lines);
        const lineColors = new Float32Array(linesCols);

        return { positions, colors: ptsColors, linePositions, lineColors };
    }, [count]);

    // Animate rotation based on frame and mouse
    useFrame((state, delta) => {
        if (groupRef.current) {
            // Auto slow rotation
            groupRef.current.rotation.y -= delta * 0.02;
            groupRef.current.rotation.x += delta * 0.01;

            // Interactive mouse rotation
            const mouseX = (state.pointer.x * Math.PI) / 20;
            const mouseY = (state.pointer.y * Math.PI) / 20;

            groupRef.current.rotation.y += (mouseX - groupRef.current.rotation.y) * 0.02;
            groupRef.current.rotation.x += (-mouseY - groupRef.current.rotation.x) * 0.02;
        }
    });

    return (
        <group ref={groupRef}>
            {/* Dots */}
            <points>
                <bufferGeometry>
                    <bufferAttribute
                        attach="attributes-position"
                        count={count}
                        array={positions}
                        itemSize={3}
                    />
                    <bufferAttribute
                        attach="attributes-color"
                        count={count}
                        array={colors}
                        itemSize={3}
                    />
                </bufferGeometry>
                <pointsMaterial
                    size={0.15}
                    vertexColors
                    transparent
                    opacity={0.8}
                    sizeAttenuation
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </points>

            {/* Connecting Lines */}
            <lineSegments>
                <bufferGeometry>
                    <bufferAttribute
                        attach="attributes-position"
                        count={linePositions.length / 3}
                        array={linePositions}
                        itemSize={3}
                    />
                    <bufferAttribute
                        attach="attributes-color"
                        count={lineColors.length / 3}
                        array={lineColors}
                        itemSize={3}
                    />
                </bufferGeometry>
                <lineBasicMaterial
                    vertexColors
                    transparent
                    opacity={0.15}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </lineSegments>
        </group>
    );
}

export default function ThreeDBackgroundScene() {
    return (
        <Canvas camera={{ position: [0, 0, 15], fov: 60 }} dpr={[1, 2]}>
            <fog attach="fog" args={['#0f172a', 10, 40]} />
            <ambientLight intensity={0.5} />
            <NetworkNodes />
        </Canvas>
    );
}
