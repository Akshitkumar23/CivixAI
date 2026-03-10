'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function FeaturesBannerBackground() {
    const mountRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!mountRef.current) return;

        const container = mountRef.current;
        const scene = new THREE.Scene();
        // Camera aspect ratio based on parent container width/height
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.z = 20;
        camera.position.y = 5;
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        const group = new THREE.Group();
        scene.add(group);

        const particleCount = 1500;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        const themeColors = [
            new THREE.Color('#ea580c'), // Saffron
            new THREE.Color('#10b981'), // Green
            new THREE.Color('#3b82f6'), // Trust Blue
            new THREE.Color('#ffffff'), // White
            new THREE.Color('#8b5cf6'), // Purple-ish
        ];

        // Create a flowing 3D wave map
        for (let i = 0; i < particleCount; i++) {
            const x = (Math.random() - 0.5) * 45;
            const z = (Math.random() - 0.5) * 45;
            const y = Math.sin(x * 0.4) * Math.cos(z * 0.4) * 1.5;

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

        const material = new THREE.PointsMaterial({
            size: 0.18,
            vertexColors: true,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const particles = new THREE.Points(geometry, material);
        group.add(particles);

        let mouseX = 0;
        let targetX = 0;

        const handleMouseMove = (event: MouseEvent) => {
            mouseX = (event.clientX - window.innerWidth / 2) * 0.001;
        };
        window.addEventListener('mousemove', handleMouseMove);

        const handleResize = () => {
            if (!container) return;
            const width = container.clientWidth;
            const height = container.clientHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        };
        window.addEventListener('resize', handleResize);

        const clock = new THREE.Clock();
        let animationFrameId: number;

        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            const time = clock.getElapsedTime();

            // Animate wave vertices to create flowing data sea effect
            const positionsAttributes = geometry.attributes.position;
            const posArray = positionsAttributes.array as Float32Array;
            for (let i = 0; i < particleCount; i++) {
                const x = posArray[i * 3];
                const z = posArray[i * 3 + 2];
                // Gently undulating sea of particles
                posArray[i * 3 + 1] = Math.sin(x * 0.2 + time * 0.5) * Math.cos(z * 0.2 + time * 0.5) * 1.5;
            }
            positionsAttributes.needsUpdate = true;

            // Slow continuous rotation of the entire group
            group.rotation.y = time * 0.03;

            // Simple parallax on camera
            targetX = mouseX * 5;
            camera.position.x += (targetX - camera.position.x) * 0.02;
            camera.lookAt(0, 0, 0);

            renderer.render(scene, camera);
        };
        animate();

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            if (container && renderer.domElement) {
                container.removeChild(renderer.domElement);
            }
            geometry.dispose();
            material.dispose();
            scene.clear();
        };
    }, []);

    return (
        <div className="absolute inset-0 w-full h-full pointer-events-none" ref={mountRef} />
    );
}
