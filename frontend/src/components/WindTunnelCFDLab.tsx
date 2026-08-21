import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Wind, Sliders, Activity, Zap, Gauge, Play, RotateCcw, Flame, CheckCircle2 } from 'lucide-react';

export const WindTunnelCFDLab: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Aerodynamic Setup Sliders
  const [frontWingAngle, setFrontWingAngle] = useState<number>(34); // degrees
  const [rearWingAngle, setRearWingAngle] = useState<number>(32);  // degrees
  const [frontRideHeight, setFrontRideHeight] = useState<number>(26); // mm
  const [rearRideHeight, setRearRideHeight] = useState<number>(78);  // mm
  const [airSpeedKmh, setAirSpeedKmh] = useState<number>(260);       // km/h
  const [showVortices, setShowVortices] = useState<boolean>(true);

  // Three.js References
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const particlesRef = useRef<THREE.Points | null>(null);
  const carGroupRef = useRef<THREE.Group | null>(null);

  // Calculated Aerodynamic Forces
  const aeroMetrics = React.useMemo(() => {
    const v_ms = (airSpeedKmh * 1000) / 3600;
    const q = 0.5 * 1.225 * v_ms * v_ms; // Dynamic pressure

    // Front downforce from front wing + ground effect
    const cl_front = 1.1 + (frontWingAngle - 25) * 0.045 - (frontRideHeight - 20) * 0.015;
    // Rear downforce from rear wing + diffuser
    const cl_rear = 1.6 + (rearWingAngle - 20) * 0.055 + (rearRideHeight - 65) * 0.008;

    const area = 1.65; // Frontal reference area m²
    const frontDownforceN = Math.round(q * cl_front * area);
    const rearDownforceN = Math.round(q * cl_rear * area);
    const totalDownforceN = frontDownforceN + rearDownforceN;

    // Drag calculation
    const cd_base = 0.72;
    const cd_wings = (frontWingAngle * 0.006) + (rearWingAngle * 0.012);
    const totalDragN = Math.round(q * (cd_base + cd_wings) * area);

    const aeroBalanceFrontPct = Math.round((frontDownforceN / totalDownforceN) * 100);
    const efficiency = Number((totalDownforceN / Math.max(1, totalDragN)).toFixed(2));
    const maxTopSpeed = Math.round(355 - (totalDragN / 24.0));

    return {
      totalDownforceN,
      frontDownforceN,
      rearDownforceN,
      totalDragN,
      aeroBalanceFrontPct,
      efficiency,
      maxTopSpeed,
    };
  }, [frontWingAngle, rearWingAngle, frontRideHeight, rearRideHeight, airSpeedKmh]);

  // Initialize Three.js Wind Tunnel
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = 480;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060911);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
    camera.position.set(-65, 32, 55);
    camera.lookAt(0, 4, 0);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambient);

    const spotlight = new THREE.SpotLight(0x00f0ff, 2.5);
    spotlight.position.set(0, 50, 20);
    spotlight.angle = Math.PI / 3;
    spotlight.penumbra = 0.5;
    scene.add(spotlight);

    const redRim = new THREE.DirectionalLight(0xff0055, 1.2);
    redRim.position.set(40, -10, -30);
    scene.add(redRim);

    // Wind Tunnel Floor Grid
    const grid = new THREE.GridHelper(180, 36, 0x00f0ff, 0x1e293b);
    grid.position.y = 0;
    scene.add(grid);

    // 3D F1 Aerodynamic Car Model
    const carGroup = new THREE.Group();
    carGroupRef.current = carGroup;

    // Car Body / Monocoque
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x0c101c, metalness: 0.9, roughness: 0.2 });
    const bodyGeo = new THREE.BoxGeometry(4.2, 1.4, 12);
    const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    bodyMesh.position.y = 1.4;
    carGroup.add(bodyMesh);

    // Nosecone
    const noseGeo = new THREE.ConeGeometry(1.6, 6, 12);
    const noseMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, metalness: 0.8, roughness: 0.2 });
    const noseMesh = new THREE.Mesh(noseGeo, noseMat);
    noseMesh.rotation.x = -Math.PI / 2;
    noseMesh.position.set(0, 1.2, -7.5);
    carGroup.add(noseMesh);

    // Front Wing
    const fwGeo = new THREE.BoxGeometry(8.5, 0.3, 2.2);
    const fwMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, metalness: 0.8 });
    const fwMesh = new THREE.Mesh(fwGeo, fwMat);
    fwMesh.position.set(0, 0.6, -9.5);
    carGroup.add(fwMesh);

    // Rear Wing
    const rwGeo = new THREE.BoxGeometry(6.5, 2.0, 1.4);
    const rwMat = new THREE.MeshStandardMaterial({ color: 0xec4899, metalness: 0.8 });
    const rwMesh = new THREE.Mesh(rwGeo, rwMat);
    rwMesh.position.set(0, 3.2, 5.8);
    carGroup.add(rwMesh);

    // Underfloor Venturi Tunnels (Ground Effect)
    const floorGeo = new THREE.BoxGeometry(5.2, 0.4, 10);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.5 });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.position.set(0, 0.4, 0);
    carGroup.add(floorMesh);

    scene.add(carGroup);

    // CFD Streamline Flow Particles
    const pCount = 2800;
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(pCount * 3);
    const pColor = new Float32Array(pCount * 3);

    for (let i = 0; i < pCount; i++) {
      pPos[i * 3] = (Math.random() - 0.5) * 16;
      pPos[i * 3 + 1] = Math.random() * 8 + 0.2;
      pPos[i * 3 + 2] = -40 + Math.random() * 80;

      // Color coding (Cyan for high speed, Pink for downforce wake)
      pColor[i * 3] = 0.0;
      pColor[i * 3 + 1] = 0.94;
      pColor[i * 3 + 2] = 1.0;
    }

    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    pGeo.setAttribute('color', new THREE.BufferAttribute(pColor, 3));

    const pMat = new THREE.PointsMaterial({
      size: 1.4,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
    });

    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);
    particlesRef.current = particles;

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (particlesRef.current) {
        const positions = particlesRef.current.geometry.attributes.position.array as Float32Array;
        const speedFactor = (airSpeedKmh / 260.0) * 1.8;

        for (let i = 0; i < pCount; i++) {
          positions[i * 3 + 2] += speedFactor; // Move particles forward along Z

          // Reset particle when past the car wake
          if (positions[i * 3 + 2] > 40) {
            positions[i * 3 + 2] = -40;
            positions[i * 3] = (Math.random() - 0.5) * 14;
            positions[i * 3 + 1] = Math.random() * 7 + 0.3;
          }

          // Flow deflection over car body
          const z = positions[i * 3 + 2];
          const x = positions[i * 3];
          if (Math.abs(x) < 4.0 && z > -10 && z < 6) {
            positions[i * 3 + 1] += 0.08 * (frontWingAngle / 30); // Upwash over front & cockpit
          }
          // Rear wing wake vortex oscillation
          if (z > 6 && Math.abs(x) < 5.0) {
            positions[i * 3] += Math.sin(positions[i * 3 + 2] * 0.4) * 0.12;
          }
        }

        particlesRef.current.geometry.attributes.position.needsUpdate = true;
      }

      if (cameraRef.current) {
        renderer.render(scene, cameraRef.current);
      }
    };

    animate();

    const handleResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;
      const w = containerRef.current.clientWidth;
      cameraRef.current.aspect = w / 480;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, 480);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [airSpeedKmh, frontWingAngle, rearWingAngle]);

  const resetToBalancedSetup = () => {
    setFrontWingAngle(34);
    setRearWingAngle(32);
    setFrontRideHeight(26);
    setRearRideHeight(78);
    setAirSpeedKmh(260);
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Wind className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">3D WIND TUNNEL & CFD AERODYNAMIC STREAMLINE LAB</span>
            <span className="text-[11px] font-mono text-slate-400">
              Interactive 3D particle vector flow, ground-effect downforce & L/D efficiency optimizer
            </span>
          </div>
        </div>

        <button
          onClick={resetToBalancedSetup}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-mono transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Balanced Setup</span>
        </button>
      </div>

      {/* Aerodynamic Force KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">TOTAL DOWNFORCE</span>
          <span className="text-2xl font-black font-mono text-apex-cyan">
            {aeroMetrics.totalDownforceN} N
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            F: {aeroMetrics.frontDownforceN}N | R: {aeroMetrics.rearDownforceN}N
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">TOTAL DRAG</span>
          <span className="text-2xl font-black font-mono text-rose-400">
            {aeroMetrics.totalDragN} N
          </span>
          <span className="text-[10px] font-mono text-slate-400">Aerodynamic resistance</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">AERO EFFICIENCY (L/D)</span>
          <span className="text-2xl font-black font-mono text-emerald-400">
            {aeroMetrics.efficiency}
          </span>
          <span className="text-[10px] font-mono text-slate-400">Downforce per Drag unit</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">AERO BALANCE</span>
          <span className="text-2xl font-black font-mono text-purple-400">
            {aeroMetrics.aeroBalanceFrontPct}% FRONT
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            {aeroMetrics.aeroBalanceFrontPct > 45 ? 'Oversteer bias' : 'Stable understeer bias'}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">ESTIMATED V-MAX</span>
          <span className="text-2xl font-black font-mono text-amber-400">
            {aeroMetrics.maxTopSpeed} KM/H
          </span>
          <span className="text-[10px] font-mono text-slate-400">Straight-line potential</span>
        </div>
      </div>

      {/* 3D WebGL Canvas & Setup Sliders Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* 3D Canvas */}
        <div className="lg:col-span-8 relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
          <div ref={containerRef} className="w-full h-[480px]" />
          <div className="absolute bottom-3 left-3 bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300">
            Airspeed: <strong className="text-apex-cyan">{airSpeedKmh} km/h</strong> • Streamline Particles:{' '}
            <strong className="text-pink-400">2,800 Active</strong>
          </div>
        </div>

        {/* Setup Tuning Controls */}
        <div className="lg:col-span-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-4">
          <span className="text-xs font-mono text-apex-cyan font-bold uppercase border-b border-slate-800 pb-2">
            AERODYNAMIC SETUP CONTROLS
          </span>

          {/* Front Wing Angle */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">Front Wing Flap Angle:</span>
              <span className="font-bold text-apex-cyan">{frontWingAngle}°</span>
            </div>
            <input
              type="range"
              min={25}
              max={45}
              value={frontWingAngle}
              onChange={(e) => setFrontWingAngle(Number(e.target.value))}
              className="w-full accent-cyan-400 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>

          {/* Rear Wing Angle */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">Rear Wing Mainplane Angle:</span>
              <span className="font-bold text-pink-400">{rearWingAngle}°</span>
            </div>
            <input
              type="range"
              min={20}
              max={42}
              value={rearWingAngle}
              onChange={(e) => setRearWingAngle(Number(e.target.value))}
              className="w-full accent-pink-400 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>

          {/* Front Ride Height */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">Front Ride Height:</span>
              <span className="font-bold text-purple-300">{frontRideHeight} mm</span>
            </div>
            <input
              type="range"
              min={20}
              max={38}
              value={frontRideHeight}
              onChange={(e) => setFrontRideHeight(Number(e.target.value))}
              className="w-full accent-purple-400 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>

          {/* Rear Ride Height */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">Rear Rake Ride Height:</span>
              <span className="font-bold text-amber-300">{rearRideHeight} mm</span>
            </div>
            <input
              type="range"
              min={65}
              max={95}
              value={rearRideHeight}
              onChange={(e) => setRearRideHeight(Number(e.target.value))}
              className="w-full accent-amber-400 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>

          {/* Airspeed Fan Velocity */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-300">Wind Tunnel Airspeed:</span>
              <span className="font-bold text-white">{airSpeedKmh} km/h</span>
            </div>
            <input
              type="range"
              min={120}
              max={350}
              step={5}
              value={airSpeedKmh}
              onChange={(e) => setAirSpeedKmh(Number(e.target.value))}
              className="w-full accent-emerald-400 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
