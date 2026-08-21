import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import { useRaceStore } from '../store/raceStore';
import { CIRCUIT_DATABASE, CircuitData } from '../data/trackGeometries';
import { CarState, TyreCompound } from '../types/race';
import {
  Camera,
  Maximize2,
  Minimize2,
  RotateCcw,
  Eye,
  Zap,
  Gauge,
  Activity,
  Layers,
  Thermometer,
  Disc,
} from 'lucide-react';

export type CameraViewMode = 'orbit' | 'isometric' | 'chase' | 'cockpit' | 'thermal';

const TEAM_LIVERY_COLORS: Record<string, { body: number; accent: number }> = {
  'Red Bull Racing': { body: 0x061148, accent: 0xde002b },
  'Ferrari': { body: 0xe80020, accent: 0xffeb00 },
  'Mercedes': { body: 0x00d2be, accent: 0xc8ccce },
  'McLaren': { body: 0xff8000, accent: 0x000000 },
  'Aston Martin': { body: 0x00665e, accent: 0xcedc00 },
  'APEX Strategy Team': { body: 0x00f0ff, accent: 0x8b5cf6 },
};

const COMPOUND_RIM_COLORS: Record<TyreCompound, number> = {
  SOFT: 0xef4444,
  MEDIUM: 0xeab308,
  HARD: 0xf8fafc,
  INTERMEDIATE: 0x22c55e,
  WET: 0x3b82f6,
};

export const Track3DDigitalTwin: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { raceState, selectedCarId, setSelectedCarId, isRunning } = useRaceStore();

  const [viewMode, setViewMode] = useState<CameraViewMode>('orbit');
  const [selectedDriverId, setSelectedDriverId] = useState<string>('car_04');
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [showHUD, setShowHUD] = useState<boolean>(true);

  const trackKey = (raceState?.track?.name?.toLowerCase().includes('monza')
    ? 'monza'
    : raceState?.track?.name?.toLowerCase().includes('spa')
    ? 'spa'
    : raceState?.track?.name?.toLowerCase().includes('monaco')
    ? 'monaco'
    : raceState?.track?.name?.toLowerCase().includes('interlagos')
    ? 'interlagos'
    : raceState?.track?.name?.toLowerCase().includes('suzuka')
    ? 'suzuka'
    : raceState?.track?.name?.toLowerCase().includes('americas') || raceState?.track?.name?.toLowerCase().includes('cota')
    ? 'cota'
    : raceState?.track?.name?.toLowerCase().includes('singapore')
    ? 'singapore'
    : raceState?.track?.name?.toLowerCase().includes('red bull') || raceState?.track?.name?.toLowerCase().includes('spielberg')
    ? 'redbullring'
    : 'silverstone') as keyof typeof CIRCUIT_DATABASE;

  const circuitData: CircuitData = CIRCUIT_DATABASE[trackKey] || CIRCUIT_DATABASE.silverstone;

  // Selected car object
  const targetedCar: CarState = useMemo(() => {
    if (!raceState?.cars?.length) {
      return {
        car_id: 'car_04',
        driver_name: 'APEX AI (You)',
        team_name: 'APEX Strategy Team',
        car_number: 44,
        is_player: true,
        position: 1,
        current_lap: 1,
        lap_progress_pct: 0,
        last_lap_time_s: null,
        best_lap_time_s: null,
        total_race_time_s: 0,
        gap_to_leader_s: 0,
        gap_to_car_ahead_s: 0,
        gap_to_car_behind_s: 0,
        tyre_compound: 'MEDIUM',
        tyre_age_laps: 0,
        tyre_wear_pct: 0,
        tyre_cliff_reached: false,
        fuel_kg: 105,
        fuel_burn_per_lap_kg: 1.8,
        driving_mode: 'NORMAL',
        in_pit: false,
        pit_count: 0,
        laps_since_last_pit: 0,
        is_dnf: false,
        dnf_reason: null,
        ers_battery_soc_pct: 85,
        ers_deploy_mode: 'BALANCED',
        speed_kmh: 305,
      };
    }
    return (
      raceState.cars.find((c) => c.car_id === selectedDriverId) ||
      raceState.cars.find((c) => c.is_player) ||
      raceState.cars[0]
    );
  }, [raceState, selectedDriverId]);

  // Scene references
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const carMeshesRef = useRef<Map<string, THREE.Group>>(new Map());
  const curveRef = useRef<THREE.CatmullRomCurve3 | null>(null);
  const particleSystemRef = useRef<THREE.Points | null>(null);

  // Mouse interaction state for Orbit controls
  const isDraggingRef = useRef<boolean>(false);
  const previousMousePosition = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const sphericalRef = useRef<{ radius: number; theta: number; phi: number }>({
    radius: 450,
    theta: Math.PI / 4,
    phi: Math.PI / 3.2,
  });

  // Generate 3D Track Spline from Circuit Waypoints
  useEffect(() => {
    if (!circuitData?.waypoints?.length) return;

    const points: THREE.Vector3[] = circuitData.waypoints.map((wp, idx) => {
      // Center waypoints around origin (SVG viewBox is 650 x 360)
      const x = (wp.x - 325) * 1.8;
      const z = (wp.y - 180) * 1.8;
      // Elevation wave based on waypoint sector & index
      const y = Math.sin((idx / circuitData.waypoints.length) * Math.PI * 2) * 18.0;
      return new THREE.Vector3(x, y, z);
    });

    curveRef.current = new THREE.CatmullRomCurve3(points, true, 'centripetal', 0.5);
  }, [circuitData]);

  // Initialize Three.js WebGL Scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 480;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x080b12);
    scene.fog = new THREE.FogExp2(0x080b12, 0.0012);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 1, 3000);
    camera.position.set(0, 320, 380);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.8);
    dirLight.position.set(250, 400, 200);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.bias = -0.0001;
    scene.add(dirLight);

    const cyanRimLight = new THREE.DirectionalLight(0x00f0ff, 0.9);
    cyanRimLight.position.set(-300, 150, -200);
    scene.add(cyanRimLight);

    // Ground Plane with Grid
    const groundGeo = new THREE.PlaneGeometry(1600, 1600, 32, 32);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -22;
    ground.receiveShadow = true;
    scene.add(ground);

    const gridHelper = new THREE.GridHelper(1400, 70, 0x1e293b, 0x0f172a);
    gridHelper.position.y = -21.8;
    scene.add(gridHelper);

    // Build 3D Track Ribbon Mesh
    if (curveRef.current) {
      const trackPoints = curveRef.current.getPoints(200);
      const trackCurve = new THREE.CatmullRomCurve3(trackPoints, true);

      // Asphalt Surface Tube
      const tubeGeo = new THREE.TubeGeometry(trackCurve, 200, 14, 12, true);
      const asphaltMat = new THREE.MeshStandardMaterial({
        color: 0x181e29,
        roughness: 0.85,
        metalness: 0.25,
      });
      const trackMesh = new THREE.Mesh(tubeGeo, asphaltMat);
      trackMesh.scale.set(1, 0.08, 1);
      trackMesh.position.y = 0;
      trackMesh.receiveShadow = true;
      scene.add(trackMesh);

      // Neon Track Edge Lines
      const edgePoints = trackCurve.getPoints(300);
      const edgeGeo = new THREE.BufferGeometry().setFromPoints(edgePoints);
      const edgeMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, linewidth: 2, transparent: true, opacity: 0.65 });
      const edgeLine = new THREE.Line(edgeGeo, edgeMat);
      edgeLine.position.y = 1.2;
      scene.add(edgeLine);
    }

    // Weather Particle Spray System
    const particleCount = 1200;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 800;
      particlePositions[i + 1] = Math.random() * 200;
      particlePositions[i + 2] = (Math.random() - 0.5) * 800;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 1.8,
      transparent: true,
      opacity: 0.35,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);
    particleSystemRef.current = particles;

    // Mouse Controls Event Listeners
    const handleMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true;
      previousMousePosition.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current || viewMode === 'chase' || viewMode === 'cockpit') return;

      const deltaX = e.clientX - previousMousePosition.current.x;
      const deltaY = e.clientY - previousMousePosition.current.y;

      sphericalRef.current.theta -= deltaX * 0.005;
      sphericalRef.current.phi = Math.max(0.1, Math.min(Math.PI / 2.05, sphericalRef.current.phi - deltaY * 0.005));

      previousMousePosition.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (viewMode === 'chase' || viewMode === 'cockpit') return;
      sphericalRef.current.radius = Math.max(120, Math.min(850, sphericalRef.current.radius + e.deltaY * 0.45));
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    domElement.addEventListener('wheel', handleWheel, { passive: false });

    // Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: w, height: h } = entry.contentRect;
        if (w > 0 && h > 0 && cameraRef.current && rendererRef.current) {
          cameraRef.current.aspect = w / h;
          cameraRef.current.updateProjectionMatrix();
          rendererRef.current.setSize(w, h);
        }
      }
    });
    resizeObserver.observe(container);

    // Animation Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsedTime = clock.getElapsedTime();

      // Animate weather particles if rain active
      if (particleSystemRef.current && raceState?.weather?.rain_intensity) {
        const rainInt = raceState.weather.rain_intensity;
        const positions = particleSystemRef.current.geometry.attributes.position.array as Float32Array;
        for (let i = 1; i < positions.length; i += 3) {
          positions[i] -= 180.0 * (0.5 + rainInt) * delta;
          if (positions[i] < -20) {
            positions[i] = 180 + Math.random() * 50;
          }
        }
        particleSystemRef.current.geometry.attributes.position.needsUpdate = true;
        (particleSystemRef.current.material as THREE.PointsMaterial).opacity = Math.min(0.8, rainInt * 0.9);
      }

      // Update Camera based on View Mode
      if (cameraRef.current) {
        if (viewMode === 'orbit') {
          const { radius, theta, phi } = sphericalRef.current;
          cameraRef.current.position.x = radius * Math.sin(phi) * Math.sin(theta);
          cameraRef.current.position.y = radius * Math.cos(phi);
          cameraRef.current.position.z = radius * Math.sin(phi) * Math.cos(theta);
          cameraRef.current.lookAt(0, 0, 0);
        } else if (viewMode === 'isometric') {
          cameraRef.current.position.set(380, 420, 380);
          cameraRef.current.lookAt(0, 0, 0);
        } else if (viewMode === 'chase' || viewMode === 'cockpit') {
          const targetMesh = carMeshesRef.current.get(selectedDriverId);
          if (targetMesh) {
            const carPos = targetMesh.position;
            const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(targetMesh.quaternion);

            if (viewMode === 'cockpit') {
              cameraRef.current.position.copy(carPos).add(new THREE.Vector3(0, 2.8, 0)).add(forward.clone().multiplyScalar(1.2));
              cameraRef.current.lookAt(carPos.clone().add(forward.clone().multiplyScalar(60)));
            } else {
              // Chase Cam
              const chaseOffset = forward.clone().multiplyScalar(-32).add(new THREE.Vector3(0, 14, 0));
              cameraRef.current.position.lerp(carPos.clone().add(chaseOffset), 0.12);
              cameraRef.current.lookAt(carPos.clone().add(forward.clone().multiplyScalar(20)));
            }
          }
        }
      }

      if (cameraRef.current) {
        renderer.render(scene, cameraRef.current);
      }
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
      domElement.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      domElement.removeEventListener('wheel', handleWheel);
      renderer.dispose();
    };
  }, [circuitData, viewMode]);

  // Synchronize 3D Cars along Circuit Curve
  useEffect(() => {
    const scene = sceneRef.current;
    const curve = curveRef.current;
    if (!scene || !curve || !raceState?.cars) return;

    const cars = raceState.cars;

    cars.forEach((car) => {
      let carGroup = carMeshesRef.current.get(car.car_id);

      // Create 3D F1 Car Mesh if not exists
      if (!carGroup) {
        carGroup = new THREE.Group();

        const livery = TEAM_LIVERY_COLORS[car.team_name] || { body: 0x3b82f6, accent: 0xffffff };

        // 1. Chassis Body
        const bodyGeo = new THREE.BoxGeometry(4.2, 1.4, 9.8);
        const bodyMat = new THREE.MeshStandardMaterial({
          color: livery.body,
          roughness: 0.25,
          metalness: 0.85,
        });
        const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
        bodyMesh.position.y = 1.1;
        bodyMesh.castShadow = true;
        carGroup.add(bodyMesh);

        // 2. Nosecone & Front Wing
        const noseGeo = new THREE.ConeGeometry(1.6, 5.5, 8);
        const noseMat = new THREE.MeshStandardMaterial({ color: livery.accent, roughness: 0.3 });
        const noseMesh = new THREE.Mesh(noseGeo, noseMat);
        noseMesh.rotation.x = -Math.PI / 2;
        noseMesh.position.set(0, 0.9, -6.2);
        carGroup.add(noseMesh);

        const frontWingGeo = new THREE.BoxGeometry(6.4, 0.25, 1.8);
        const frontWingMesh = new THREE.Mesh(frontWingGeo, noseMat);
        frontWingMesh.position.set(0, 0.5, -8.0);
        carGroup.add(frontWingMesh);

        // 3. Rear Wing & DRS Flap
        const rearWingGeo = new THREE.BoxGeometry(5.2, 1.8, 1.2);
        const rearWingMesh = new THREE.Mesh(rearWingGeo, bodyMat);
        rearWingMesh.position.set(0, 2.4, 4.8);
        carGroup.add(rearWingMesh);

        // 4. Halo & Cockpit
        const haloGeo = new THREE.TorusGeometry(1.1, 0.2, 8, 16, Math.PI);
        const haloMat = new THREE.MeshStandardMaterial({ color: 0x111827, metalness: 0.9 });
        const haloMesh = new THREE.Mesh(haloGeo, haloMat);
        haloMesh.rotation.x = -Math.PI / 2;
        haloMesh.position.set(0, 2.2, -0.6);
        carGroup.add(haloMesh);

        // 5. Wheels & Glowing Brake Discs
        const rimColor = COMPOUND_RIM_COLORS[car.tyre_compound] || 0xeab308;
        const wheelGeo = new THREE.CylinderGeometry(1.1, 1.1, 1.0, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.9 });
        const rimMat = new THREE.MeshBasicMaterial({ color: rimColor });

        const wheelPositions = [
          [-2.6, 1.1, -4.2], // FL
          [2.6, 1.1, -4.2],  // FR
          [-2.7, 1.1, 3.8],  // RL
          [2.7, 1.1, 3.8],   // RR
        ];

        wheelPositions.forEach(([wx, wy, wz]) => {
          const wheelMesh = new THREE.Mesh(wheelGeo, wheelMat);
          wheelMesh.rotation.z = Math.PI / 2;
          wheelMesh.position.set(wx, wy, wz);

          // Glowing brake disc
          const brakeGeo = new THREE.CylinderGeometry(0.75, 0.75, 0.3, 12);
          const brakeMat = new THREE.MeshStandardMaterial({
            color: 0xff3300,
            emissive: 0xff2200,
            emissiveIntensity: 0.8,
          });
          const brakeMesh = new THREE.Mesh(brakeGeo, brakeMat);
          brakeMesh.position.set(0, 0.2, 0);
          wheelMesh.add(brakeMesh);

          carGroup!.add(wheelMesh);
        });

        // 6. Driver Tag Marker (Billboard)
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 48;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.fillStyle = car.is_player ? '#00f0ff' : '#ffffff';
          ctx.font = 'bold 24px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(`P${car.position} ${car.driver_name.split(' ')[1] || car.driver_name}`, 64, 34);
        }
        const tagTexture = new THREE.CanvasTexture(canvas);
        const tagMat = new THREE.SpriteMaterial({ map: tagTexture, transparent: true });
        const tagSprite = new THREE.Sprite(tagMat);
        tagSprite.position.set(0, 5.5, 0);
        tagSprite.scale.set(14, 5.2, 1);
        carGroup.add(tagSprite);

        scene.add(carGroup);
        carMeshesRef.current.set(car.car_id, carGroup);
      }

      // Calculate spline position based on lap progress (0.0 - 1.0)
      const progress = ((car.lap_progress_pct || 0) / 100.0) % 1.0;
      const targetPos = curve.getPointAt(Math.max(0, Math.min(1, progress)));
      const tangent = curve.getTangentAt(Math.max(0, Math.min(1, progress)));

      // Offset cars slightly across track width according to position
      const lateralOffset = ((car.position % 3) - 1) * 3.2;
      const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      targetPos.add(normal.multiplyScalar(lateralOffset));

      carGroup.position.copy(targetPos);

      // Orient car along track tangent
      const lookTarget = targetPos.clone().add(tangent);
      carGroup.lookAt(lookTarget);
    });
  }, [raceState]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const resetCamera = () => {
    sphericalRef.current = { radius: 450, theta: Math.PI / 4, phi: Math.PI / 3.2 };
    setViewMode('orbit');
  };

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl flex flex-col">
      {/* Top 3D Mission Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 z-10 text-xs">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-bold text-slate-200">
            <Layers className="w-4 h-4 text-apex-cyan animate-pulse" />
            <span>3D SPATIAL DIGITAL TWIN</span>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-apex-cyan/20 text-apex-cyan border border-apex-cyan/40">
            {circuitData.name.toUpperCase()}
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
            {circuitData.flag} {circuitData.lengthKm} KM
          </span>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setViewMode('orbit')}
            className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-all ${
              viewMode === 'orbit'
                ? 'bg-apex-cyan text-black font-bold shadow-sm shadow-cyan-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            3D ORBIT
          </button>
          <button
            onClick={() => setViewMode('isometric')}
            className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-all ${
              viewMode === 'isometric'
                ? 'bg-apex-cyan text-black font-bold shadow-sm shadow-cyan-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            ISOMETRIC
          </button>
          <button
            onClick={() => setViewMode('chase')}
            className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-all ${
              viewMode === 'chase'
                ? 'bg-purple-500 text-black font-bold shadow-sm shadow-purple-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            CHASE CAM
          </button>
          <button
            onClick={() => setViewMode('cockpit')}
            className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-all ${
              viewMode === 'cockpit'
                ? 'bg-rose-500 text-black font-bold shadow-sm shadow-rose-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            COCKPIT HUD
          </button>
        </div>

        {/* Target Driver Selector & Utilities */}
        <div className="flex items-center gap-2">
          <select
            value={selectedDriverId}
            onChange={(e) => setSelectedDriverId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-slate-200 text-xs font-mono focus:outline-none focus:border-apex-cyan"
          >
            {raceState?.cars?.map((c) => (
              <option key={c.car_id} value={c.car_id}>
                P{c.position} - {c.driver_name} {c.is_player ? '(YOU)' : ''}
              </option>
            )) || <option value="car_04">P1 - APEX AI (YOU)</option>}
          </select>

          <button
            onClick={resetCamera}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all"
            title="Reset Camera Orientation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* WebGL Canvas Container */}
      <div
        ref={containerRef}
        className="relative w-full h-[480px] lg:h-[560px] bg-slate-950 cursor-grab active:cursor-grabbing"
      />

      {/* Cockpit / Chase Cam HUD Overlay */}
      {(viewMode === 'chase' || viewMode === 'cockpit') && showHUD && (
        <div className="absolute bottom-4 left-4 right-4 pointer-events-none flex items-end justify-between gap-4 z-20">
          {/* Driver Telemetry Glass HUD */}
          <div className="bg-black/75 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-4 shadow-2xl flex flex-col gap-2 min-w-[280px]">
            <div className="flex items-center justify-between border-b border-slate-700/60 pb-1.5">
              <span className="font-mono font-bold text-apex-cyan text-sm">
                P{targetedCar.position} • {targetedCar.driver_name.toUpperCase()}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {targetedCar.team_name}
              </span>
            </div>

            {/* Speed & RPM Gauge */}
            <div className="flex items-baseline justify-between">
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black font-mono text-white tracking-tighter">
                  {targetedCar.speed_kmh || 312}
                </span>
                <span className="text-[11px] font-mono text-slate-400">KM/H</span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-lg font-black font-mono text-amber-400">
                  GEAR {targetedCar.speed_kmh && targetedCar.speed_kmh > 260 ? '7' : '5'}
                </span>
                <span className="text-[10px] font-mono text-emerald-400">11,850 RPM</span>
              </div>
            </div>

            {/* ERS State of Charge Bar */}
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="flex items-center gap-1 text-purple-300">
                  <Zap className="w-3 h-3 text-purple-400" />
                  ERS BATTERY (SoC)
                </span>
                <span className="font-bold text-white">{targetedCar.ers_battery_soc_pct || 85}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-600 to-apex-cyan transition-all duration-300"
                  style={{ width: `${targetedCar.ers_battery_soc_pct || 85}%` }}
                />
              </div>
            </div>

            {/* DRS & Dirty Air Status */}
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono pt-1">
              <div
                className={`px-2 py-1 rounded text-center font-bold ${
                  targetedCar.gap_to_car_ahead_s < 1.0 && targetedCar.position > 1
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse'
                    : 'bg-slate-800/80 text-slate-500'
                }`}
              >
                DRS {targetedCar.gap_to_car_ahead_s < 1.0 && targetedCar.position > 1 ? 'ACTIVE' : 'STANDBY'}
              </div>
              <div
                className={`px-2 py-1 rounded text-center font-bold ${
                  targetedCar.in_dirty_air
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'bg-slate-800/80 text-slate-400'
                }`}
              >
                {targetedCar.in_dirty_air ? 'DIRTY AIR WAKE' : 'CLEAN AIR'}
              </div>
            </div>
          </div>

          {/* G-Force Ball & Tyre Temps */}
          <div className="bg-black/75 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-4 shadow-2xl flex flex-col items-center gap-2">
            <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">LATERAL G-FORCE</span>
            <div className="relative w-20 h-20 rounded-full border border-slate-700 flex items-center justify-center">
              <div className="w-full h-0.5 bg-slate-800 absolute" />
              <div className="h-full w-0.5 bg-slate-800 absolute" />
              <div
                className="w-3.5 h-3.5 rounded-full bg-apex-cyan shadow-lg shadow-cyan-500/50 absolute transition-all duration-150"
                style={{
                  transform: `translate(${Math.sin((targetedCar.lap_progress_pct || 0) * 0.1) * 25}px, ${
                    Math.cos((targetedCar.lap_progress_pct || 0) * 0.1) * 15
                  }px)`,
                }}
              />
            </div>
            <span className="font-mono text-xs font-bold text-slate-200">3.4 G CORNERING</span>
          </div>
        </div>
      )}
    </div>
  );
};
