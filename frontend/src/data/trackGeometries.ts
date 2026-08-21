/**
 * Bespoke SVG Track Geometries, Sector Splits, DRS Zones & Corner Coordinates
 * for Silverstone, Monza, Spa-Francorchamps, Monaco, and Interlagos.
 */

export interface TrackSector {
  id: string;
  name: string;
  color: string;
  path: string;
}

export interface DRSZone {
  id: string;
  name: string;
  path: string;
}

export interface TrackCorner {
  number: number;
  name: string;
  x: number;
  y: number;
}

export interface TrackWaypoint {
  pct: number; // 0 to 100% of lap
  x: number;
  y: number;
  sector: 1 | 2 | 3;
  speedKmh?: number;
}

export interface CircuitData {
  id: string;
  name: string;
  country: string;
  flag: string;
  lengthKm: number;
  baseLapS: number;
  viewBox: string;
  fullPath: string;
  pitLanePath: string;
  startFinishLine: { x1: number; y1: number; x2: number; y2: number };
  sectors: TrackSector[];
  drsZones: DRSZone[];
  corners: TrackCorner[];
  waypoints: TrackWaypoint[];
}

export const CIRCUIT_DATABASE: Record<string, CircuitData> = {
  silverstone: {
    id: 'silverstone',
    name: 'Silverstone Circuit',
    country: 'Great Britain',
    flag: '🇬🇧',
    lengthKm: 5.891,
    baseLapS: 88.5,
    viewBox: '0 0 650 360',
    fullPath: 'M 140 250 C 90 250 60 190 75 140 C 90 90 150 70 210 65 C 270 60 320 100 370 85 C 430 70 510 40 580 95 C 615 125 610 180 560 210 C 510 240 450 210 400 230 C 350 250 330 300 260 300 C 200 300 170 250 140 250 Z',
    pitLanePath: 'M 110 230 C 130 238 160 238 180 235',
    startFinishLine: { x1: 140, y1: 235, x2: 140, y2: 265 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Abbey to Copse)', color: '#00f0ff', path: 'M 140 250 C 90 250 60 190 75 140 C 90 90 150 70 210 65' },
      { id: 's2', name: 'Sector 2 (Maggotts to Stowe)', color: '#f59e0b', path: 'M 210 65 C 270 60 320 100 370 85 C 430 70 510 40 580 95' },
      { id: 's3', name: 'Sector 3 (Vale to Club)', color: '#a855f7', path: 'M 580 95 C 615 125 610 180 560 210 C 510 240 450 210 400 230 C 350 250 330 300 260 300 C 200 300 170 250 140 250' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Wellington Straight', path: 'M 75 140 C 90 90 150 70 200 66' },
      { id: 'drs2', name: 'Hangar Straight', path: 'M 430 70 C 490 50 540 60 575 90' },
    ],
    corners: [
      { number: 1, name: 'Abbey', x: 105, y: 240 },
      { number: 3, name: 'Village', x: 70, y: 155 },
      { number: 6, name: 'Brooklands', x: 170, y: 68 },
      { number: 9, name: 'Copse', x: 260, y: 68 },
      { number: 10, name: 'Maggotts', x: 340, y: 92 },
      { number: 11, name: 'Becketts', x: 385, y: 80 },
      { number: 15, name: 'Stowe', x: 575, y: 120 },
      { number: 16, name: 'Vale', x: 530, y: 220 },
      { number: 18, name: 'Club', x: 360, y: 240 },
    ],
    waypoints: [
      { pct: 0, x: 140, y: 250, sector: 1, speedKmh: 285 },
      { pct: 8, x: 95, y: 235, sector: 1, speedKmh: 210 },
      { pct: 15, x: 70, y: 170, sector: 1, speedKmh: 115 },
      { pct: 24, x: 100, y: 105, sector: 1, speedKmh: 290 },
      { pct: 32, x: 175, y: 68, sector: 1, speedKmh: 170 },
      { pct: 40, x: 270, y: 62, sector: 2, speedKmh: 295 },
      { pct: 48, x: 360, y: 88, sector: 2, speedKmh: 260 },
      { pct: 56, x: 440, y: 70, sector: 2, speedKmh: 310 },
      { pct: 65, x: 550, y: 65, sector: 2, speedKmh: 325 },
      { pct: 72, x: 580, y: 130, sector: 3, speedKmh: 195 },
      { pct: 80, x: 520, y: 225, sector: 3, speedKmh: 120 },
      { pct: 88, x: 420, y: 220, sector: 3, speedKmh: 225 },
      { pct: 95, x: 260, y: 300, sector: 3, speedKmh: 270 },
    ],
  },

  monza: {
    id: 'monza',
    name: 'Autodromo Nazionale Monza',
    country: 'Italy',
    flag: '🇮🇹',
    lengthKm: 5.793,
    baseLapS: 81.0,
    viewBox: '0 0 650 360',
    fullPath: 'M 120 280 L 120 100 C 120 60 160 50 200 70 L 290 120 C 330 140 370 110 400 90 L 530 65 C 580 55 610 85 610 135 C 610 190 560 220 500 240 L 260 280 C 200 290 160 290 120 280 Z',
    pitLanePath: 'M 100 260 L 100 120',
    startFinishLine: { x1: 105, y1: 220, x2: 135, y2: 220 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Rettifilo & Curva Grande)', color: '#00f0ff', path: 'M 120 280 L 120 100 C 120 60 160 50 200 70' },
      { id: 's2', name: 'Sector 2 (Variante Roggia & Lesmo)', color: '#f59e0b', path: 'M 200 70 L 290 120 C 330 140 370 110 400 90 L 530 65' },
      { id: 's3', name: 'Sector 3 (Ascari & Parabolica)', color: '#a855f7', path: 'M 530 65 C 580 55 610 85 610 135 C 610 190 560 220 500 240 L 260 280 C 200 290 160 290 120 280' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Main Pit Straight', path: 'M 120 270 L 120 120' },
      { id: 'drs2', name: 'Serraglio Straight', path: 'M 400 90 L 520 68' },
    ],
    corners: [
      { number: 1, name: 'Variante del Rettifilo', x: 120, y: 90 },
      { number: 3, name: 'Curva Grande', x: 200, y: 70 },
      { number: 4, name: 'Variante della Roggia', x: 300, y: 130 },
      { number: 6, name: 'Lesmo 1', x: 370, y: 105 },
      { number: 7, name: 'Lesmo 2', x: 420, y: 85 },
      { number: 8, name: 'Variante Ascari', x: 560, y: 70 },
      { number: 11, name: 'Curva Parabolica', x: 570, y: 200 },
    ],
    waypoints: [
      { pct: 0, x: 120, y: 220, sector: 1, speedKmh: 345 },
      { pct: 12, x: 120, y: 100, sector: 1, speedKmh: 80 },
      { pct: 25, x: 180, y: 65, sector: 1, speedKmh: 290 },
      { pct: 38, x: 290, y: 120, sector: 2, speedKmh: 125 },
      { pct: 48, x: 380, y: 100, sector: 2, speedKmh: 185 },
      { pct: 60, x: 470, y: 75, sector: 2, speedKmh: 330 },
      { pct: 72, x: 565, y: 75, sector: 3, speedKmh: 175 },
      { pct: 85, x: 580, y: 185, sector: 3, speedKmh: 240 },
      { pct: 94, x: 380, y: 265, sector: 3, speedKmh: 320 },
    ],
  },

  spa: {
    id: 'spa',
    name: 'Circuit de Spa-Francorchamps',
    country: 'Belgium',
    flag: '🇧🇪',
    lengthKm: 7.004,
    baseLapS: 104.5,
    viewBox: '0 0 650 360',
    fullPath: 'M 100 240 L 90 190 C 95 150 130 150 160 140 C 200 130 250 90 320 60 C 370 40 430 40 480 60 C 530 80 570 120 580 170 C 590 220 540 260 480 270 C 430 280 390 250 340 260 C 290 270 260 310 200 310 C 150 310 110 280 100 240 Z',
    pitLanePath: 'M 115 250 L 110 180',
    startFinishLine: { x1: 85, y1: 220, x2: 115, y2: 220 },
    sectors: [
      { id: 's1', name: 'Sector 1 (La Source & Raidillon)', color: '#00f0ff', path: 'M 100 240 L 90 190 C 95 150 130 150 160 140 C 200 130 250 90 320 60' },
      { id: 's2', name: 'Sector 2 (Kemmel to Pouhon)', color: '#f59e0b', path: 'M 320 60 C 370 40 430 40 480 60 C 530 80 570 120 580 170' },
      { id: 's3', name: 'Sector 3 (Blanchimont & Bus Stop)', color: '#a855f7', path: 'M 580 170 C 590 220 540 260 480 270 C 430 280 390 250 340 260 C 290 270 260 310 200 310 C 150 310 110 280 100 240' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Kemmel Straight', path: 'M 200 125 C 250 85 300 65 370 45' },
      { id: 'drs2', name: 'Start/Finish Straight', path: 'M 150 310 C 120 290 105 260 95 210' },
    ],
    corners: [
      { number: 1, name: 'La Source', x: 88, y: 170 },
      { number: 3, name: 'Eau Rouge', x: 145, y: 145 },
      { number: 4, name: 'Raidillon', x: 180, y: 130 },
      { number: 5, name: 'Les Combes', x: 400, y: 45 },
      { number: 8, name: 'Bruxelles', x: 490, y: 70 },
      { number: 10, name: 'Pouhon', x: 575, y: 150 },
      { number: 17, name: 'Blanchimont', x: 420, y: 275 },
      { number: 19, name: 'Bus Stop Chicane', x: 170, y: 310 },
    ],
    waypoints: [
      { pct: 0, x: 95, y: 220, sector: 1, speedKmh: 270 },
      { pct: 10, x: 88, y: 165, sector: 1, speedKmh: 75 },
      { pct: 20, x: 160, y: 140, sector: 1, speedKmh: 305 },
      { pct: 35, x: 330, y: 55, sector: 2, speedKmh: 335 },
      { pct: 48, x: 440, y: 45, sector: 2, speedKmh: 140 },
      { pct: 60, x: 565, y: 130, sector: 2, speedKmh: 260 },
      { pct: 75, x: 520, y: 250, sector: 3, speedKmh: 290 },
      { pct: 88, x: 320, y: 260, sector: 3, speedKmh: 315 },
      { pct: 96, x: 170, y: 310, sector: 3, speedKmh: 85 },
    ],
  },

  monaco: {
    id: 'monaco',
    name: 'Circuit de Monaco',
    country: 'Monaco',
    flag: '🇲🇨',
    lengthKm: 3.337,
    baseLapS: 73.2,
    viewBox: '0 0 650 360',
    fullPath: 'M 160 290 L 160 170 C 160 120 200 90 260 80 C 330 70 380 90 410 130 C 430 160 410 190 370 190 C 330 190 330 230 380 240 C 440 250 540 230 580 180 C 600 150 590 100 550 80 C 510 60 460 70 430 90 L 450 140 C 490 210 520 290 440 310 C 350 330 250 310 160 290 Z',
    pitLanePath: 'M 180 295 L 180 190',
    startFinishLine: { x1: 145, y1: 240, x2: 175, y2: 240 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Sainte Dévote & Casino)', color: '#00f0ff', path: 'M 160 290 L 160 170 C 160 120 200 90 260 80 C 330 70 380 90 410 130' },
      { id: 's2', name: 'Sector 2 (Mirabeau, Hairpin & Tunnel)', color: '#f59e0b', path: 'M 410 130 C 430 160 410 190 370 190 C 330 190 330 230 380 240 C 440 250 540 230 580 180' },
      { id: 's3', name: 'Sector 3 (Tabac, Swimming Pool & Rascasse)', color: '#a855f7', path: 'M 580 180 C 600 150 590 100 550 80 C 510 60 460 70 430 90 L 450 140 C 490 210 520 290 440 310 C 350 330 250 310 160 290' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Boulevard Albert 1er', path: 'M 160 280 L 160 180' },
    ],
    corners: [
      { number: 1, name: 'Sainte Dévote', x: 160, y: 155 },
      { number: 3, name: 'Massenet', x: 275, y: 80 },
      { number: 4, name: 'Casino Square', x: 360, y: 85 },
      { number: 6, name: 'Grand Hotel Hairpin', x: 350, y: 195 },
      { number: 8, name: 'Portier', x: 380, y: 240 },
      { number: 9, name: 'The Tunnel', x: 530, y: 220 },
      { number: 10, name: 'Nouvelle Chicane', x: 575, y: 170 },
      { number: 12, name: 'Tabac', x: 530, y: 80 },
      { number: 18, name: 'Rascasse', x: 260, y: 310 },
    ],
    waypoints: [
      { pct: 0, x: 160, y: 240, sector: 1, speedKmh: 275 },
      { pct: 15, x: 160, y: 155, sector: 1, speedKmh: 90 },
      { pct: 30, x: 280, y: 80, sector: 1, speedKmh: 195 },
      { pct: 45, x: 355, y: 190, sector: 2, speedKmh: 50 },
      { pct: 60, x: 490, y: 235, sector: 2, speedKmh: 280 },
      { pct: 75, x: 575, y: 160, sector: 3, speedKmh: 80 },
      { pct: 88, x: 480, y: 180, sector: 3, speedKmh: 190 },
      { pct: 96, x: 270, y: 310, sector: 3, speedKmh: 85 },
    ],
  },

  interlagos: {
    id: 'interlagos',
    name: 'Autódromo de Interlagos',
    country: 'Brazil',
    flag: '🇧🇷',
    lengthKm: 4.309,
    baseLapS: 70.5,
    viewBox: '0 0 650 360',
    fullPath: 'M 180 80 C 130 90 90 140 100 190 C 110 240 170 270 230 260 L 370 260 C 440 260 520 220 550 160 C 570 120 540 70 480 70 C 430 70 410 120 360 140 C 310 160 270 120 250 90 C 230 70 210 70 180 80 Z',
    pitLanePath: 'M 200 95 C 240 85 300 85 350 90',
    startFinishLine: { x1: 300, y1: 65, x2: 300, y2: 95 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Senna S & Curva do Sol)', color: '#00f0ff', path: 'M 300 80 L 180 80 C 130 90 90 140 100 190' },
      { id: 's2', name: 'Sector 2 (Reta Oposta to Ferradura)', color: '#f59e0b', path: 'M 100 190 C 110 240 170 270 230 260 L 370 260 C 440 260 520 220 550 160' },
      { id: 's3', name: 'Sector 3 (Junção & Arquibancadas)', color: '#a855f7', path: 'M 550 160 C 570 120 540 70 480 70 C 430 70 410 120 360 140 C 310 160 270 120 250 90 C 230 70 210 70 300 80' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Main Straight', path: 'M 450 70 L 220 78' },
      { id: 'drs2', name: 'Reta Oposta', path: 'M 100 190 C 120 245 180 260 260 260' },
    ],
    corners: [
      { number: 1, name: 'Senna S (Turn 1)', x: 135, y: 110 },
      { number: 2, name: 'Senna S (Turn 2)', x: 100, y: 160 },
      { number: 3, name: 'Curva do Sol', x: 120, y: 225 },
      { number: 4, name: 'Descida do Lago', x: 270, y: 260 },
      { number: 6, name: 'Ferradura', x: 480, y: 240 },
      { number: 8, name: 'Bico de Pato', x: 530, y: 115 },
      { number: 12, name: 'Junção', x: 380, y: 135 },
    ],
    waypoints: [
      { pct: 0, x: 300, y: 80, sector: 1, speedKmh: 325 },
      { pct: 12, x: 130, y: 110, sector: 1, speedKmh: 110 },
      { pct: 24, x: 110, y: 210, sector: 1, speedKmh: 245 },
      { pct: 38, x: 230, y: 260, sector: 2, speedKmh: 310 },
      { pct: 52, x: 450, y: 250, sector: 2, speedKmh: 180 },
      { pct: 68, x: 535, y: 130, sector: 2, speedKmh: 120 },
      { pct: 82, x: 420, y: 110, sector: 3, speedKmh: 210 },
      { pct: 94, x: 340, y: 80, sector: 3, speedKmh: 315 },
    ],
  },

  suzuka: {
    id: 'suzuka',
    name: 'Suzuka International Racing Course',
    country: 'Japan',
    flag: '🇯🇵',
    lengthKm: 5.807,
    baseLapS: 89.2,
    viewBox: '0 0 650 360',
    fullPath: 'M 140 280 L 140 180 C 140 130 180 100 230 100 C 270 100 290 140 330 140 C 370 140 390 100 440 90 C 490 80 540 120 540 180 C 540 240 480 270 410 270 C 350 270 320 220 280 220 C 240 220 210 260 170 280 Z',
    pitLanePath: 'M 160 285 L 160 190',
    startFinishLine: { x1: 125, y1: 240, x2: 155, y2: 240 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Esses & Dunlop)', color: '#00f0ff', path: 'M 140 280 L 140 180 C 140 130 180 100 230 100 C 270 100 290 140 330 140' },
      { id: 's2', name: 'Sector 2 (Degner, Hairpin & Spoon)', color: '#f59e0b', path: 'M 330 140 C 370 140 390 100 440 90 C 490 80 540 120 540 180' },
      { id: 's3', name: 'Sector 3 (130R & Casio Triangle)', color: '#a855f7', path: 'M 540 180 C 540 240 480 270 410 270 C 350 270 320 220 280 220 C 240 220 210 260 170 280' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Pit Straight', path: 'M 140 275 L 140 190' },
    ],
    corners: [
      { number: 1, name: 'Turn 1 & 2', x: 140, y: 155 },
      { number: 3, name: 'S-Curves (Turn 3)', x: 190, y: 105 },
      { number: 7, name: 'Dunlop Curve', x: 290, y: 130 },
      { number: 8, name: 'Degner 1', x: 370, y: 110 },
      { number: 11, name: 'Hairpin', x: 490, y: 95 },
      { number: 13, name: 'Spoon Curve', x: 535, y: 175 },
      { number: 15, name: '130R', x: 410, y: 265 },
      { number: 16, name: 'Casio Triangle', x: 250, y: 245 },
    ],
    waypoints: [
      { pct: 0, x: 140, y: 240, sector: 1, speedKmh: 310 },
      { pct: 15, x: 145, y: 150, sector: 1, speedKmh: 140 },
      { pct: 30, x: 240, y: 105, sector: 1, speedKmh: 215 },
      { pct: 45, x: 360, y: 120, sector: 2, speedKmh: 185 },
      { pct: 60, x: 480, y: 95, sector: 2, speedKmh: 75 },
      { pct: 75, x: 535, y: 200, sector: 3, speedKmh: 190 },
      { pct: 88, x: 400, y: 265, sector: 3, speedKmh: 315 },
      { pct: 96, x: 220, y: 260, sector: 3, speedKmh: 80 },
    ],
  },

  cota: {
    id: 'cota',
    name: 'Circuit of the Americas',
    country: 'United States',
    flag: '🇺🇸',
    lengthKm: 5.513,
    baseLapS: 94.5,
    viewBox: '0 0 650 360',
    fullPath: 'M 160 300 L 160 120 C 160 70 220 60 260 90 L 330 140 C 370 170 420 150 460 120 L 550 80 C 580 80 600 120 590 170 C 570 240 500 280 430 260 C 380 240 330 250 280 280 Z',
    pitLanePath: 'M 180 295 L 180 140',
    startFinishLine: { x1: 145, y1: 220, x2: 175, y2: 220 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Hilltop Turn 1 & Esses)', color: '#00f0ff', path: 'M 160 300 L 160 120 C 160 70 220 60 260 90 L 330 140' },
      { id: 's2', name: 'Sector 2 (Back Straight to Turn 12)', color: '#f59e0b', path: 'M 330 140 C 370 170 420 150 460 120 L 550 80 C 580 80 600 120 590 170' },
      { id: 's3', name: 'Sector 3 (Stadium Section & Carousel)', color: '#a855f7', path: 'M 590 170 C 570 240 500 280 430 260 C 380 240 330 250 280 280 Z' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Back Straight', path: 'M 460 120 L 550 80' },
      { id: 'drs2', name: 'Main Pit Straight', path: 'M 160 280 L 160 140' },
    ],
    corners: [
      { number: 1, name: 'Big Red Turn 1', x: 170, y: 80 },
      { number: 3, name: 'Esses (Turn 3-5)', x: 270, y: 105 },
      { number: 11, name: 'Turn 11 Hairpin', x: 420, y: 145 },
      { number: 12, name: 'Turn 12 Heavy Braking', x: 570, y: 90 },
      { number: 15, name: 'Stadium Complex', x: 550, y: 210 },
      { number: 17, name: 'Multi-Apex Carousel', x: 430, y: 260 },
      { number: 20, name: 'Turn 20 Final', x: 230, y: 290 },
    ],
    waypoints: [
      { pct: 0, x: 160, y: 220, sector: 1, speedKmh: 315 },
      { pct: 12, x: 175, y: 80, sector: 1, speedKmh: 85 },
      { pct: 28, x: 290, y: 120, sector: 1, speedKmh: 240 },
      { pct: 45, x: 430, y: 140, sector: 2, speedKmh: 95 },
      { pct: 60, x: 550, y: 85, sector: 2, speedKmh: 335 },
      { pct: 75, x: 560, y: 220, sector: 3, speedKmh: 110 },
      { pct: 88, x: 410, y: 255, sector: 3, speedKmh: 190 },
      { pct: 96, x: 210, y: 290, sector: 3, speedKmh: 125 },
    ],
  },

  singapore: {
    id: 'singapore',
    name: 'Marina Bay Street Circuit',
    country: 'Singapore',
    flag: '🇸🇬',
    lengthKm: 4.940,
    baseLapS: 96.0,
    viewBox: '0 0 650 360',
    fullPath: 'M 140 280 L 140 120 C 140 80 180 70 220 80 L 320 80 C 360 80 390 110 390 150 L 390 200 C 390 240 430 250 480 250 L 560 250 C 600 250 610 200 600 160 C 580 100 520 80 470 80 L 430 80 C 400 80 380 120 350 140 L 260 200 C 210 240 170 270 140 280 Z',
    pitLanePath: 'M 160 270 L 160 140',
    startFinishLine: { x1: 125, y1: 200, x2: 155, y2: 200 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Sheares to Republic Blvd)', color: '#00f0ff', path: 'M 140 280 L 140 120 C 140 80 180 70 220 80 L 320 80' },
      { id: 's2', name: 'Sector 2 (Raffles to Padang)', color: '#f59e0b', path: 'M 320 80 C 360 80 390 110 390 150 L 390 200 C 390 240 430 250 480 250' },
      { id: 's3', name: 'Sector 3 (Esplanade to Marina Bay Waterfront)', color: '#a855f7', path: 'M 480 250 L 560 250 C 600 250 610 200 600 160 C 580 100 520 80 470 80 L 430 80 C 400 80 380 120 350 140 L 260 200 C 210 240 170 270 140 280' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Pit Straight', path: 'M 140 270 L 140 140' },
      { id: 'drs2', name: 'Raffles Avenue', path: 'M 220 80 L 320 80' },
    ],
    corners: [
      { number: 1, name: 'Sheares (Turn 1-3)', x: 160, y: 90 },
      { number: 5, name: 'Turn 5 Republic Blvd', x: 330, y: 85 },
      { number: 7, name: 'Memorial Corner (Turn 7)', x: 390, y: 150 },
      { number: 9, name: 'Padang (Turn 9)', x: 400, y: 230 },
      { number: 14, name: 'Connaught Drive', x: 570, y: 230 },
      { number: 16, name: 'Esplanade (Turn 16-17)', x: 580, y: 120 },
      { number: 19, name: 'Turn 19 Grandstand', x: 330, y: 155 },
    ],
    waypoints: [
      { pct: 0, x: 140, y: 200, sector: 1, speedKmh: 285 },
      { pct: 15, x: 160, y: 95, sector: 1, speedKmh: 90 },
      { pct: 30, x: 280, y: 80, sector: 1, speedKmh: 295 },
      { pct: 45, x: 390, y: 165, sector: 2, speedKmh: 110 },
      { pct: 60, x: 490, y: 250, sector: 2, speedKmh: 275 },
      { pct: 75, x: 590, y: 160, sector: 3, speedKmh: 105 },
      { pct: 88, x: 420, y: 90, sector: 3, speedKmh: 260 },
      { pct: 96, x: 220, y: 240, sector: 3, speedKmh: 140 },
    ],
  },

  redbullring: {
    id: 'redbullring',
    name: 'Red Bull Ring (Spielberg)',
    country: 'Austria',
    flag: '🇦🇹',
    lengthKm: 4.318,
    baseLapS: 65.2,
    viewBox: '0 0 650 360',
    fullPath: 'M 140 280 L 140 100 C 140 60 190 50 240 60 L 460 70 C 510 70 540 110 520 150 L 450 230 C 410 270 360 280 300 270 L 220 280 Z',
    pitLanePath: 'M 160 270 L 160 120',
    startFinishLine: { x1: 125, y1: 200, x2: 155, y2: 200 },
    sectors: [
      { id: 's1', name: 'Sector 1 (Niki Lauda Kurve to Remus)', color: '#00f0ff', path: 'M 140 280 L 140 100 C 140 60 190 50 240 60' },
      { id: 's2', name: 'Sector 2 (Remus Hairpin to Rauch)', color: '#f59e0b', path: 'M 240 60 L 460 70 C 510 70 540 110 520 150' },
      { id: 's3', name: 'Sector 3 (Würth Kurve & Jochen Rindt)', color: '#a855f7', path: 'M 520 150 L 450 230 C 410 270 360 280 300 270 L 220 280 Z' },
    ],
    drsZones: [
      { id: 'drs1', name: 'Main Straight', path: 'M 140 270 L 140 120' },
      { id: 'drs2', name: 'Remus Straight', path: 'M 230 60 L 450 70' },
      { id: 'drs3', name: 'Downhill Straight', path: 'M 520 150 L 460 220' },
    ],
    corners: [
      { number: 1, name: 'Turn 1 (Niki Lauda Kurve)', x: 150, y: 75 },
      { number: 3, name: 'Turn 3 (Remus Hairpin)', x: 260, y: 60 },
      { number: 4, name: 'Turn 4 (Schlossgold)', x: 490, y: 80 },
      { number: 6, name: 'Turn 6 (Rauch Kurve)', x: 510, y: 170 },
      { number: 9, name: 'Turn 9 (Jochen Rindt)', x: 380, y: 265 },
      { number: 10, name: 'Turn 10 (Red Bull Mobile)', x: 230, y: 280 },
    ],
    waypoints: [
      { pct: 0, x: 140, y: 200, sector: 1, speedKmh: 315 },
      { pct: 15, x: 150, y: 80, sector: 1, speedKmh: 140 },
      { pct: 30, x: 280, y: 60, sector: 1, speedKmh: 75 },
      { pct: 48, x: 470, y: 75, sector: 2, speedKmh: 320 },
      { pct: 65, x: 515, y: 160, sector: 2, speedKmh: 210 },
      { pct: 80, x: 440, y: 240, sector: 3, speedKmh: 240 },
      { pct: 94, x: 250, y: 275, sector: 3, speedKmh: 290 },
    ],
  },
};

