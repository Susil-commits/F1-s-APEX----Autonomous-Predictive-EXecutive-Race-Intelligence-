import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Timer, Zap, Play, RotateCcw, Activity, CheckCircle2, AlertTriangle, Disc } from 'lucide-react';
import confetti from 'canvas-confetti';

export const PitStop3DCrewLab: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Pit Stop Simulation States
  const [pitState, setPitState] = useState<'IDLE' | 'APPROACHING' | 'JACKS_UP' | 'WHEELS_OFF' | 'WHEELS_ON' | 'TORQUED' | 'RELEASED'>('IDLE');
  const [stopTimeMs, setStopTimeMs] = useState<number>(0);
  const [reactionTimeMs, setReactionTimeMs] = useState<number>(0);
  const [bestTimeMs, setBestTimeMs] = useState<number>(1820);
  const [targetCompound, setTargetCompound] = useState<'SOFT' | 'MEDIUM' | 'HARD' | 'INTER'>('SOFT');

  // Wheel Gun Torque telemetry
  const [torqueFL, setTorqueFL] = useState<number>(0);
  const [torqueFR, setTorqueFR] = useState<number>(0);
  const [torqueRL, setTorqueRL] = useState<number>(0);
  const [torqueRR, setTorqueRR] = useState<number>(0);

  // Three.js refs
  const sceneRef = useRef<THREE.Scene | null>(null);
  const carMeshRef = useRef<THREE.Group | null>(null);
  const jacksRef = useRef<{ front: THREE.Mesh; rear: THREE.Mesh } | null>(null);
  const wheelsRef = useRef<THREE.Mesh[]>([]);

  // Initialize Three.js Pit Box
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = 440;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070b14);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(40, width / height, 1, 1000);
    camera.position.set(-36, 18, 32);
    camera.lookAt(0, 2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Pit Box Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambient);

    const overheadLight = new THREE.DirectionalLight(0x00f0ff, 2.0);
    overheadLight.position.set(0, 30, 0);
    scene.add(overheadLight);

    const redLight = new THREE.PointLight(0xff0055, 1.5, 50);
    redLight.position.set(20, 10, 10);
    scene.add(redLight);

    // Pit Lane Concrete Ground & Yellow Box Markings
    const floorGeo = new THREE.PlaneGeometry(80, 40);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.8 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    // Yellow Box Markings
    const boxGeo = new THREE.RingGeometry(9, 9.4, 4);
    const boxMat = new THREE.MeshBasicMaterial({ color: 0xfacc15, side: THREE.DoubleSide });
    const box = new THREE.Mesh(boxGeo, boxMat);
    box.rotation.x = -Math.PI / 2;
    box.rotation.z = Math.PI / 4;
    box.position.y = 0.02;
    scene.add(box);

    // 3D F1 Car Group
    const carGroup = new THREE.Group();
    carMeshRef.current = carGroup;

    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x090d16, metalness: 0.8, roughness: 0.2 });
    const bodyMesh = new THREE.Mesh(new THREE.BoxGeometry(4.5, 1.2, 13), bodyMat);
    bodyMesh.position.y = 1.2;
    carGroup.add(bodyMesh);

    // Wings
    const wingMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, metalness: 0.6 });
    const fwMesh = new THREE.Mesh(new THREE.BoxGeometry(7.8, 0.3, 2.0), wingMat);
    fwMesh.position.set(0, 0.6, -7.0);
    carGroup.add(fwMesh);

    const rwMesh = new THREE.Mesh(new THREE.BoxGeometry(6.2, 1.8, 1.2), wingMat);
    rwMesh.position.set(0, 2.6, 6.2);
    carGroup.add(rwMesh);

    // 4 Wheels
    wheelsRef.current = [];
    const wheelPositions = [
      [-3.2, 1.0, -4.2], // FL
      [3.2, 1.0, -4.2],  // FR
      [-3.2, 1.1, 4.2],  // RL
      [3.2, 1.1, 4.2],   // RR
    ];

    wheelPositions.forEach((pos) => {
      const wMat = new THREE.MeshStandardMaterial({ color: 0x1c1917, roughness: 0.6 });
      const wMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 1.2, 16), wMat);
      wMesh.rotation.z = Math.PI / 2;
      wMesh.position.set(pos[0], pos[1], pos[2]);
      carGroup.add(wMesh);
      wheelsRef.current.push(wMesh);
    });

    scene.add(carGroup);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, []);

  // Pit Stop Simulation Sequence Trigger
  const triggerPitStopDrill = () => {
    if (pitState !== 'IDLE' && pitState !== 'RELEASED') return;

    setPitState('APPROACHING');
    setStopTimeMs(0);
    setTorqueFL(0);
    setTorqueFR(0);
    setTorqueRL(0);
    setTorqueRR(0);

    const startTime = performance.now();

    // Sequence timing
    setTimeout(() => {
      setPitState('JACKS_UP');
      if (carMeshRef.current) carMeshRef.current.position.y = 0.5; // Lift car
    }, 400);

    setTimeout(() => {
      setPitState('WHEELS_OFF');
      setTorqueFL(450);
      setTorqueFR(450);
      setTorqueRL(450);
      setTorqueRR(450);
    }, 900);

    setTimeout(() => {
      setPitState('WHEELS_ON');
    }, 1400);

    setTimeout(() => {
      setPitState('TORQUED');
      setTorqueFL(455);
      setTorqueFR(452);
      setTorqueRL(448);
      setTorqueRR(450);
    }, 1750);

    setTimeout(() => {
      setPitState('RELEASED');
      if (carMeshRef.current) carMeshRef.current.position.y = 0; // Drop car

      const finalElapsed = Math.round(performance.now() - startTime);
      setStopTimeMs(finalElapsed);

      if (finalElapsed < bestTimeMs) {
        setBestTimeMs(finalElapsed);
      }

      // Celebrate sub-2.0s stop
      if (finalElapsed < 2200) {
        confetti({ particleCount: 80, spread: 60, origin: { y: 0.6 } });
      }
    }, 1980);
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Timer className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              3D PIT CREW DIGITAL TWIN & SUB-2.0s WHEEL GUN LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              4-corner wheel gun torque telemetry (Nm), jack drop latency & reaction time drill
            </span>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={triggerPitStopDrill}
          disabled={pitState !== 'IDLE' && pitState !== 'RELEASED'}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all shadow-lg active:scale-95 ${
            pitState === 'IDLE' || pitState === 'RELEASED'
              ? 'bg-amber-500 hover:bg-amber-400 text-black shadow-amber-500/30 cursor-pointer'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{pitState === 'IDLE' || pitState === 'RELEASED' ? 'BOX CAR NOW (EXECUTE DRILL)' : 'PIT STOP IN PROGRESS...'}</span>
        </button>
      </div>

      {/* KPI Stop Time Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">STATIONARY TIME</span>
          <span className="text-2xl font-black font-mono text-amber-400">
            {stopTimeMs > 0 ? `${(stopTimeMs / 1000).toFixed(2)}s` : '0.00s'}
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            {stopTimeMs > 0 && stopTimeMs < 2000 ? '⚡ WORLD CLASS STOP' : 'Standing time'}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">BEST SESSION RECORD</span>
          <span className="text-2xl font-black font-mono text-emerald-400">
            {(bestTimeMs / 1000).toFixed(2)}s
          </span>
          <span className="text-[10px] font-mono text-slate-400">Target benchmark: 1.80s</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">CREW STATUS</span>
          <span className="text-2xl font-black font-mono text-apex-cyan uppercase">
            {pitState}
          </span>
          <span className="text-[10px] font-mono text-slate-400">20-person crew synchronized</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">TARGET COMPOUND</span>
          <span className="text-2xl font-black font-mono text-rose-400 uppercase">
            {targetCompound}
          </span>
          <span className="text-[10px] font-mono text-slate-400">Heated tyre blankets off</span>
        </div>
      </div>

      {/* 3D WebGL Canvas & Wheel Gun Gauges */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* 3D Pit Box Viewport */}
        <div className="lg:col-span-8 relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
          <div ref={containerRef} className="w-full h-[440px]" />
          <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300">
            Pit Box Gantry: <strong className="text-amber-400">{pitState}</strong> • Jack State:{' '}
            <strong className="text-emerald-400">{pitState === 'JACKS_UP' || pitState === 'WHEELS_OFF' || pitState === 'WHEELS_ON' || pitState === 'TORQUED' ? 'UP' : 'DOWN'}</strong>
          </div>
        </div>

        {/* 4-Corner Wheel Gun Telemetry */}
        <div className="lg:col-span-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3">
          <span className="text-xs font-mono text-amber-400 font-bold uppercase border-b border-slate-800 pb-2">
            4-CORNER WHEEL GUN TORQUE (NM)
          </span>

          <div className="grid grid-cols-2 gap-2.5">
            {/* FL */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-col">
              <span className="text-[10px] font-mono text-slate-400">FL WHEEL GUN</span>
              <span className="text-xl font-bold font-mono text-white">{torqueFL} Nm</span>
              <span className="text-[9px] font-mono text-emerald-400 font-bold">
                {torqueFL >= 445 ? '✓ LOCKED' : 'STANDBY'}
              </span>
            </div>

            {/* FR */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-col">
              <span className="text-[10px] font-mono text-slate-400">FR WHEEL GUN</span>
              <span className="text-xl font-bold font-mono text-white">{torqueFR} Nm</span>
              <span className="text-[9px] font-mono text-emerald-400 font-bold">
                {torqueFR >= 445 ? '✓ LOCKED' : 'STANDBY'}
              </span>
            </div>

            {/* RL */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-col">
              <span className="text-[10px] font-mono text-slate-400">RL WHEEL GUN</span>
              <span className="text-xl font-bold font-mono text-white">{torqueRL} Nm</span>
              <span className="text-[9px] font-mono text-emerald-400 font-bold">
                {torqueRL >= 445 ? '✓ LOCKED' : 'STANDBY'}
              </span>
            </div>

            {/* RR */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-col">
              <span className="text-[10px] font-mono text-slate-400">RR WHEEL GUN</span>
              <span className="text-xl font-bold font-mono text-white">{torqueRR} Nm</span>
              <span className="text-[9px] font-mono text-emerald-400 font-bold">
                {torqueRR >= 445 ? '✓ LOCKED' : 'STANDBY'}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 flex flex-col gap-1 text-[11px] font-mono text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">Target Torque:</span>
              <span className="font-bold text-white">450.0 Nm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Nut Thread Safety:</span>
              <span className="font-bold text-emerald-400">100% OK</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Pit Release Gantry:</span>
              <span className="font-bold text-amber-400">{pitState === 'RELEASED' ? 'GREEN LIGHT' : 'HOLD RED'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
