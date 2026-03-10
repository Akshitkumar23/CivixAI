'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function CoreAIHeroBackground() {
    const mountRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!mountRef.current) return;

        const scene = new THREE.Scene();
        // Camera aspect ratio based on parent container width/height
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
        camera.position.z = 25; // adjusted for better view of network

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        mountRef.current.appendChild(renderer.domElement);

        // Group to hold the network
        const networkGroup = new THREE.Group();
        scene.add(networkGroup);

        const particleCount = 350; // Increased for better network feel
        const radius = 12;

        // 1. Create Particles with Tricolor & Trust Blue themes
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        const themeColors = [
            new THREE.Color('#ea580c'), // Saffron
            new THREE.Color('#10b981'), // Green
            new THREE.Color('#3b82f6'), // Trust Blue
            new THREE.Color('#ffffff'), // White
            new THREE.Color('#60a5fa'), // Light Blue
        ];

        for (let i = 0; i < particleCount; i++) {
            // spherical distribution
            const theta = Math.random() * 2 * Math.PI;
            const phi = Math.acos(Math.random() * 2 - 1);

            const x = radius * Math.sin(phi) * Math.cos(theta);
            const y = radius * Math.sin(phi) * Math.sin(theta);
            const z = radius * Math.cos(phi);

            positions[i * 3] = x;
            positions[i * 3 + 1] = y;
            positions[i * 3 + 2] = z;

            const color = themeColors[Math.floor(Math.random() * themeColors.length)];
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const pMaterial = new THREE.PointsMaterial({
            size: 0.2,
            vertexColors: true,
            transparent: true,
            opacity: 0.9,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const particles = new THREE.Points(geometry, pMaterial);
        networkGroup.add(particles);

        // 2. Create connections (Lines) between close nodes
        const linePositions = [];
        const lineColors = [];

        for (let i = 0; i < particleCount; i++) {
            for (let j = i + 1; j < particleCount; j++) {
                const dx = positions[i * 3] - positions[j * 3];
                const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
                const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (dist < 3.5) { // Connection threshold length
                    linePositions.push(
                        positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2],
                        positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]
                    );

                    // Subtle cyan/blue for lines
                    lineColors.push(
                        0.2, 0.4, 0.8,
                        0.2, 0.4, 0.8
                    );
                }
            }
        }

        const lineGeometry = new THREE.BufferGeometry();
        lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
        lineGeometry.setAttribute('color', new THREE.Float32BufferAttribute(lineColors, 3));

        const lineMaterial = new THREE.LineBasicMaterial({
            vertexColors: true,
            transparent: true,
            opacity: 0.15,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
        networkGroup.add(lines);

        // Mouse Parallax Interaction (More subtle for Govt theme)
        let mouseX = 0;
        let mouseY = 0;
        let targetX = 0;
        let targetY = 0;

        const handleMouseMove = (event: MouseEvent) => {
            // normalized coordinates relative to the window
            mouseX = (event.clientX - window.innerWidth / 2) * 0.001;
            mouseY = (event.clientY - window.innerHeight / 2) * 0.001;
        };
        window.addEventListener('mousemove', handleMouseMove);

        const handleResize = () => {
            if (!mountRef.current) return;
            const width = window.innerWidth;
            const height = window.innerHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        };
        window.addEventListener('resize', handleResize);

        const clock = new THREE.Clock();
        let animationFrameId: number;

        let timeRotationY = 0;
        let timeRotationX = 0;

        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            const delta = clock.getDelta();

            // Store the continuously increasing base rotation
            timeRotationY += delta * 0.08;
            timeRotationX += delta * 0.03;

            // Fluid Parallax hover effect based on mouse
            targetX = mouseX * 0.8;
            targetY = mouseY * 0.8;

            // The final rotation is the continuous rotation PLUS the mouse offset
            const finalTargetY = timeRotationY + targetX;
            const finalTargetX = timeRotationX + targetY;

            // Smoothly interpolate towards the combined target
            networkGroup.rotation.y += 0.05 * (finalTargetY - networkGroup.rotation.y);
            networkGroup.rotation.x += 0.05 * (finalTargetX - networkGroup.rotation.x);

            renderer.render(scene, camera);
        };
        animate();

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            if (mountRef.current && renderer.domElement) {
                mountRef.current.removeChild(renderer.domElement);
            }
            scene.clear();
        };
    }, []);

    // Full absolute coverage inside relative parent container
    return (
        <div className="absolute inset-0 w-full h-full pointer-events-none" ref={mountRef} />
    );
}
