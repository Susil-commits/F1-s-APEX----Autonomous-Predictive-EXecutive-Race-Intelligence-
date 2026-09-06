import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface F1Aerodynamics3DProps {
  className?: string;
  theme?: 'dark' | 'light';
  accentColor?: string;
}

export const F1Aerodynamics3D: React.FC<F1Aerodynamics3DProps> = ({
  className = 'w-full h-full',
  theme = 'dark',
  accentColor = '#E10600',
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 1.8, 4.2);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Group for F1 chassis and aerodynamics
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Aerodynamic streamline curves
    const streamlinesCount = 42;
    const streamlineGeometries: THREE.BufferGeometry[] = [];
    const streamlineMaterial = new THREE.LineBasicMaterial({
      color: new THREE.Color(accentColor),
      transparent: true,
      opacity: theme === 'dark' ? 0.65 : 0.45,
      blending: theme === 'dark' ? THREE.AdditiveBlending : THREE.NormalBlending,
    });

    const particlesPerLine = 36;
    const particlePositions: Float32Array = new Float32Array(streamlinesCount * particlesPerLine * 3);
    const particleSpeeds: number[] = [];

    let pIdx = 0;
    for (let i = 0; i < streamlinesCount; i++) {
      const offsetX = (Math.random() - 0.5) * 2.2;
      const offsetY = 0.1 + Math.random() * 0.9;
      const speed = 0.03 + Math.random() * 0.04;

      const points: THREE.Vector3[] = [];
      for (let j = 0; j < particlesPerLine; j++) {
        const t = (j / particlesPerLine) * 6 - 3; // Z from -3 to +3
        // Aerodynamic deflection around cockpit (Z ~ 0)
        const deflectionY = Math.exp(-t * t * 1.2) * 0.45;
        const deflectionX = Math.sign(offsetX || 1) * Math.exp(-t * t * 0.8) * 0.25;

        const x = offsetX + deflectionX;
        const y = offsetY + deflectionY;
        const z = t;

        points.push(new THREE.Vector3(x, y, z));
        particlePositions[pIdx++] = x;
        particlePositions[pIdx++] = y;
        particlePositions[pIdx++] = z;
      }
      particleSpeeds.push(speed);

      const curve = new THREE.CatmullRomCurve3(points);
      const geom = new THREE.BufferGeometry().setFromPoints(curve.getPoints(50));
      const line = new THREE.Line(geom, streamlineMaterial);
      rootGroup.add(line);
      streamlineGeometries.push(geom);
    }

    // Interactive Particle Stream
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: theme === 'dark' ? 0x00F0FF : 0x0284C7,
      size: 0.045,
      transparent: true,
      opacity: 0.85,
    });
    const particleSystem = new THREE.Points(particleGeometry, particleMat);
    rootGroup.add(particleSystem);

    // Sleek Minimalist F1 Chassis Wireframe
    const carMat = new THREE.MeshStandardMaterial({
      color: theme === 'dark' ? 0x12151E : 0xD1D5DB,
      wireframe: true,
      transparent: true,
      opacity: theme === 'dark' ? 0.35 : 0.25,
    });

    // Main nose & tub
    const noseGeom = new THREE.ConeGeometry(0.35, 2.4, 6);
    noseGeom.rotateX(Math.PI / 2);
    const nose = new THREE.Mesh(noseGeom, carMat);
    nose.position.set(0, 0.25, -0.6);
    rootGroup.add(nose);

    // Sidepods
    const podGeom = new THREE.BoxGeometry(0.45, 0.3, 1.4);
    const leftPod = new THREE.Mesh(podGeom, carMat);
    leftPod.position.set(0.65, 0.25, 0.2);
    const rightPod = new THREE.Mesh(podGeom, carMat);
    rightPod.position.set(-0.65, 0.25, 0.2);
    rootGroup.add(leftPod);
    rootGroup.add(rightPod);

    // Rear Wing
    const wingGeom = new THREE.BoxGeometry(1.6, 0.06, 0.4);
    const rearWing = new THREE.Mesh(wingGeom, carMat);
    rearWing.position.set(0, 0.75, 1.2);
    rootGroup.add(rearWing);

    // Front Wing
    const fWingGeom = new THREE.BoxGeometry(1.8, 0.04, 0.3);
    const frontWing = new THREE.Mesh(fWingGeom, carMat);
    frontWing.position.set(0, 0.12, -1.8);
    rootGroup.add(frontWing);

    // Ambient & Directional Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, theme === 'dark' ? 0.6 : 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(3, 5, 2);
    scene.add(dirLight);

    // Mouse Interaction
    let targetRotY = 0;
    let targetRotX = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetRotY = x * 0.35;
      targetRotX = -y * 0.15;
    };

    window.addEventListener('mousemove', handleMouseMove);

    // Animation Loop
    let animationId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const delta = clock.getDelta();

      // Smooth camera / group rotation tracking
      rootGroup.rotation.y += (targetRotY - rootGroup.rotation.y) * 0.05;
      rootGroup.rotation.x += (targetRotX - rootGroup.rotation.x) * 0.05;

      // Flow particles along Z
      const positions = particleGeometry.attributes.position.array as Float32Array;
      const count = positions.length / 3;
      for (let i = 0; i < count; i++) {
        const zIdx = i * 3 + 2;
        positions[zIdx] += (particleSpeeds[i % streamlinesCount] || 0.03) * 60 * delta;
        if (positions[zIdx] > 3.0) {
          positions[zIdx] = -3.0;
        }
      }
      particleGeometry.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // Resize handler
    const handleResize = () => {
      if (!container) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      particleGeometry.dispose();
      particleMat.dispose();
      streamlineGeometries.forEach((g) => g.dispose());
      streamlineMaterial.dispose();
      carMat.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [theme, accentColor]);

  return <div ref={mountRef} className={className} style={{ minHeight: '340px' }} />;
};

export default F1Aerodynamics3D;
