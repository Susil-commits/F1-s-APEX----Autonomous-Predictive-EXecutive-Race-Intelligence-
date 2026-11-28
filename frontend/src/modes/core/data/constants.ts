export interface GrandPrix {
  id: string;
  name: string;
  circuit: string;
  round: number;
  flag: string;
  laps: number;
  distanceKm: number;
  downforce: 'HIGH' | 'MEDIUM' | 'LOW' | 'MAXIMUM';
  city: string;
  country: string;
}

export const GRAND_PRIX_LIST: GrandPrix[] = [
  { id: 'silverstone', name: 'British GP', circuit: 'Silverstone Circuit', round: 12, flag: '🇬🇧', laps: 52, distanceKm: 5.891, downforce: 'HIGH', city: 'Silverstone', country: 'United Kingdom' },
  { id: 'monza', name: 'Italian GP', circuit: 'Autodromo Nazionale Monza', round: 16, flag: '🇮🇹', laps: 53, distanceKm: 5.793, downforce: 'LOW', city: 'Monza', country: 'Italy' },
  { id: 'spa', name: 'Belgian GP', circuit: 'Circuit de Spa-Francorchamps', round: 14, flag: '🇧🇪', laps: 44, distanceKm: 7.004, downforce: 'MEDIUM', city: 'Spa', country: 'Belgium' },
  { id: 'monaco', name: 'Monaco GP', circuit: 'Circuit de Monaco', round: 8, flag: '🇲🇨', laps: 78, distanceKm: 3.337, downforce: 'MAXIMUM', city: 'Monte Carlo', country: 'Monaco' },
  { id: 'bahrain', name: 'Bahrain GP', circuit: 'Bahrain International Circuit', round: 1, flag: '🇧🇭', laps: 57, distanceKm: 5.412, downforce: 'MEDIUM', city: 'Sakhir', country: 'Bahrain' },
  { id: 'suzuka', name: 'Japanese GP', circuit: 'Suzuka International Racing Course', round: 4, flag: '🇯🇵', laps: 53, distanceKm: 5.807, downforce: 'HIGH', city: 'Suzuka', country: 'Japan' },
  { id: 'interlagos', name: 'São Paulo GP', circuit: 'Autódromo José Carlos Pace', round: 21, flag: '🇧🇷', laps: 71, distanceKm: 4.309, downforce: 'MEDIUM', city: 'São Paulo', country: 'Brazil' },
  { id: 'albert_park', name: 'Australian GP', circuit: 'Albert Park Circuit', round: 3, flag: '🇦🇺', laps: 58, distanceKm: 5.278, downforce: 'MEDIUM', city: 'Melbourne', country: 'Australia' },
  { id: 'jeddah', name: 'Saudi Arabian GP', circuit: 'Jeddah Corniche Circuit', round: 2, flag: '🇸🇦', laps: 50, distanceKm: 6.174, downforce: 'LOW', city: 'Jeddah', country: 'Saudi Arabia' },
  { id: 'shanghai', name: 'Chinese GP', circuit: 'Shanghai International Circuit', round: 5, flag: '🇨🇳', laps: 56, distanceKm: 5.451, downforce: 'MEDIUM', city: 'Shanghai', country: 'China' },
  { id: 'miami', name: 'Miami GP', circuit: 'Miami International Autodrome', round: 6, flag: '🇺🇸', laps: 57, distanceKm: 5.412, downforce: 'MEDIUM', city: 'Miami', country: 'United States' },
  { id: 'imola', name: 'Emilia Romagna GP', circuit: 'Autodromo Enzo e Dino Ferrari', round: 7, flag: '🇮🇹', laps: 63, distanceKm: 4.909, downforce: 'HIGH', city: 'Imola', country: 'Italy' },
  { id: 'villeneuve', name: 'Canadian GP', circuit: 'Circuit Gilles Villeneuve', round: 9, flag: '🇨🇦', laps: 70, distanceKm: 4.361, downforce: 'LOW', city: 'Montreal', country: 'Canada' },
  { id: 'catalunya', name: 'Spanish GP', circuit: 'Circuit de Barcelona-Catalunya', round: 10, flag: '🇪🇸', laps: 66, distanceKm: 4.657, downforce: 'HIGH', city: 'Barcelona', country: 'Spain' },
  { id: 'red_bull_ring', name: 'Austrian GP', circuit: 'Red Bull Ring', round: 11, flag: '🇦🇹', laps: 71, distanceKm: 4.318, downforce: 'MEDIUM', city: 'Spielberg', country: 'Austria' },
  { id: 'hungaroring', name: 'Hungarian GP', circuit: 'Hungaroring', round: 13, flag: '🇭🇺', laps: 70, distanceKm: 4.381, downforce: 'MAXIMUM', city: 'Budapest', country: 'Hungary' },
  { id: 'zandvoort', name: 'Dutch GP', circuit: 'Circuit Zandvoort', round: 15, flag: '🇳🇱', laps: 72, distanceKm: 4.259, downforce: 'MAXIMUM', city: 'Zandvoort', country: 'Netherlands' },
  { id: 'baku', name: 'Azerbaijan GP', circuit: 'Baku City Circuit', round: 17, flag: '🇦🇿', laps: 51, distanceKm: 6.003, downforce: 'LOW', city: 'Baku', country: 'Azerbaijan' },
  { id: 'marina_bay', name: 'Singapore GP', circuit: 'Marina Bay Street Circuit', round: 18, flag: '🇸🇬', laps: 62, distanceKm: 4.940, downforce: 'MAXIMUM', city: 'Singapore', country: 'Singapore' },
  { id: 'americas', name: 'United States GP', circuit: 'Circuit of the Americas', round: 19, flag: '🇺🇸', laps: 56, distanceKm: 5.513, downforce: 'HIGH', city: 'Austin', country: 'United States' },
  { id: 'rodriguez', name: 'Mexico City GP', circuit: 'Autódromo Hermanos Rodríguez', round: 20, flag: '🇲🇽', laps: 71, distanceKm: 4.304, downforce: 'MAXIMUM', city: 'Mexico City', country: 'Mexico' },
  { id: 'vegas', name: 'Las Vegas GP', circuit: 'Las Vegas Strip Circuit', round: 22, flag: '🇺🇸', laps: 50, distanceKm: 6.201, downforce: 'LOW', city: 'Las Vegas', country: 'United States' },
  { id: 'losail', name: 'Qatar GP', circuit: 'Lusail International Circuit', round: 23, flag: '🇶🇦', laps: 57, distanceKm: 5.419, downforce: 'HIGH', city: 'Lusail', country: 'Qatar' },
  { id: 'yas_marina', name: 'Abu Dhabi GP', circuit: 'Yas Marina Circuit', round: 24, flag: '🇦🇪', laps: 58, distanceKm: 5.281, downforce: 'MEDIUM', city: 'Abu Dhabi', country: 'UAE' },
];

export interface DriverItem {
  code: string;
  firstName: string;
  lastName: string;
  team: string;
  number: number;
  color: string;
  country: string;
  defaultGrid: number;
  photo: string;
}

export const DRIVERS_LIST: DriverItem[] = [
  { code: 'VER', firstName: 'Max', lastName: 'VERSTAPPEN', team: 'Red Bull Racing', number: 1, color: '#3671C6', country: '🇳🇱', defaultGrid: 1, photo: '/f1/drivers/VER.webp' },
  { code: 'NOR', firstName: 'Lando', lastName: 'NORRIS', team: 'McLaren', number: 4, color: '#FF8000', country: '🇬🇧', defaultGrid: 2, photo: '/f1/drivers/NOR.webp' },
  { code: 'LEC', firstName: 'Charles', lastName: 'LECLERC', team: 'Ferrari', number: 16, color: '#E80020', country: '🇲🇨', defaultGrid: 3, photo: '/f1/drivers/LEC.webp' },
  { code: 'PIA', firstName: 'Oscar', lastName: 'PIASTRI', team: 'McLaren', number: 81, color: '#FF8000', country: '🇦🇺', defaultGrid: 4, photo: '/f1/drivers/PIA.webp' },
  { code: 'HAM', firstName: 'Lewis', lastName: 'HAMILTON', team: 'Ferrari', number: 44, color: '#E80020', country: '🇬🇧', defaultGrid: 5, photo: '/f1/drivers/HAM.webp' },
  { code: 'RUS', firstName: 'George', lastName: 'RUSSELL', team: 'Mercedes', number: 63, color: '#00A19B', country: '🇬🇧', defaultGrid: 6, photo: '/f1/drivers/RUS.webp' },
  { code: 'ANT', firstName: 'Kimi', lastName: 'ANTONELLI', team: 'Mercedes', number: 12, color: '#00A19B', country: '🇮🇹', defaultGrid: 7, photo: '/f1/drivers/ANT.webp' },
  { code: 'SAI', firstName: 'Carlos', lastName: 'SAINZ', team: 'Williams', number: 55, color: '#64C4FF', country: '🇪🇸', defaultGrid: 8, photo: '/f1/drivers/SAI.webp' },
  { code: 'HAD', firstName: 'Isack', lastName: 'HADJAR', team: 'Red Bull Racing', number: 6, color: '#3671C6', country: '🇫🇷', defaultGrid: 9, photo: '/f1/drivers/HAD.webp' },
  { code: 'ALO', firstName: 'Fernando', lastName: 'ALONSO', team: 'Aston Martin', number: 14, color: '#229971', country: '🇪🇸', defaultGrid: 10, photo: '/f1/drivers/ALO.webp' },
  { code: 'STR', firstName: 'Lance', lastName: 'STROLL', team: 'Aston Martin', number: 18, color: '#229971', country: '🇨🇦', defaultGrid: 11, photo: '/f1/drivers/STR.webp' },
  { code: 'LAW', firstName: 'Liam', lastName: 'LAWSON', team: 'RB', number: 30, color: '#6692FF', country: '🇳🇿', defaultGrid: 12, photo: '/f1/drivers/LAW.webp' },
  { code: 'ALB', firstName: 'Alexander', lastName: 'ALBON', team: 'Williams', number: 23, color: '#64C4FF', country: '🇹🇭', defaultGrid: 13, photo: '/f1/drivers/ALB.webp' },
  { code: 'HUL', firstName: 'Nico', lastName: 'HULKENBERG', team: 'Audi', number: 27, color: '#52E252', country: '🇩🇪', defaultGrid: 14, photo: '/f1/drivers/HUL.webp' },
  { code: 'BOR', firstName: 'Gabriel', lastName: 'BORTOLETO', team: 'Audi', number: 5, color: '#52E252', country: '🇧🇷', defaultGrid: 15, photo: '/f1/drivers/BOR.webp' },
  { code: 'GAS', firstName: 'Pierre', lastName: 'GASLY', team: 'Alpine', number: 10, color: '#0093CC', country: '🇫🇷', defaultGrid: 16, photo: '/f1/drivers/GAS.webp' },
  { code: 'COL', firstName: 'Franco', lastName: 'COLAPINTO', team: 'Alpine', number: 43, color: '#0093CC', country: '🇦🇷', defaultGrid: 17, photo: '/f1/drivers/COL.webp' },
  { code: 'BEA', firstName: 'Oliver', lastName: 'BEARMAN', team: 'Haas F1 Team', number: 87, color: '#B6BABD', country: '🇬🇧', defaultGrid: 18, photo: '/f1/drivers/BEA.webp' },
  { code: 'OCO', firstName: 'Esteban', lastName: 'OCON', team: 'Haas F1 Team', number: 31, color: '#B6BABD', country: '🇫🇷', defaultGrid: 19, photo: '/f1/drivers/OCO.webp' },
  { code: 'TSU', firstName: 'Yuki', lastName: 'TSUNODA', team: 'RB', number: 22, color: '#6692FF', country: '🇯🇵', defaultGrid: 20, photo: '/f1/drivers/TSU.webp' },
  { code: 'LIN', firstName: 'Arvid', lastName: 'LINDBLAD', team: 'RB', number: 41, color: '#6692FF', country: '🇬🇧', defaultGrid: 19, photo: '/f1/drivers/LIN.webp' },
  { code: 'BOT', firstName: 'Valtteri', lastName: 'BOTTAS', team: 'Cadillac F1 Team', number: 77, color: '#94A3B8', country: '🇫🇮', defaultGrid: 17, photo: '/f1/drivers/BOT.webp' },
  { code: 'PER', firstName: 'Sergio', lastName: 'PEREZ', team: 'Cadillac F1 Team', number: 11, color: '#94A3B8', country: '🇲🇽', defaultGrid: 18, photo: '/f1/drivers/PER.webp' },
];

export interface OfficialSponsor {
  name: string;
  logo: string;
}

export const OFFICIAL_SPONSORS: OfficialSponsor[] = [
  { name: 'Pirelli', logo: '/f1/pirelli.webp' },
  { name: 'Aramco', logo: '/f1/aramco.webp' },
  { name: 'AWS', logo: '/f1/AWS GLOBAL.webp' },
  { name: 'DHL', logo: '/f1/dhl.webp' },
  { name: 'Qatar Airways', logo: '/f1/qatar.webp' },
  { name: 'Crypto.com', logo: '/f1/crypto.com.webp' },
  { name: 'Salesforce', logo: '/f1/salesforce.webp' },
  { name: 'Lenovo', logo: '/f1/lenovo.webp' },
  { name: 'Puma', logo: '/f1/puma.webp' },
  { name: 'Santander', logo: '/f1/santander.webp' },
];

export const F1_CDN_FALLBACK: Record<string, string> = {
  VER: 'https://media.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png',
  NOR: 'https://media.formula1.com/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png',
  LEC: 'https://media.formula1.com/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png',
  PIA: 'https://media.formula1.com/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png',
  SAI: 'https://media.formula1.com/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png',
  HAM: 'https://media.formula1.com/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png',
  RUS: 'https://media.formula1.com/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png',
  ANT: 'https://www.formula1.com/content/dam/fom-website/drivers/2025Drivers/antonelli.jpg',
  PER: 'https://media.formula1.com/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png',
  ALO: 'https://media.formula1.com/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png',
  STR: 'https://media.formula1.com/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png',
  TSU: 'https://media.formula1.com/content/dam/fom-website/drivers/Y/YUKTSU01_Yuki_Tsunoda/yuktsu01.png',
  HUL: 'https://media.formula1.com/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png',
  ALB: 'https://media.formula1.com/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png',
  RIC: 'https://media.formula1.com/content/dam/fom-website/drivers/D/DANRIC01_Daniel_Ricciardo/danric01.png',
  GAS: 'https://media.formula1.com/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png',
  OCO: 'https://media.formula1.com/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png',
  MAG: 'https://media.formula1.com/content/dam/fom-website/drivers/K/KEVMAG01_Kevin_Magnussen/kevmag01.png',
  ZHO: 'https://media.formula1.com/content/dam/fom-website/drivers/G/GUAZHO01_Guanyu_Zhou/guazho01.png',
  BOT: 'https://media.formula1.com/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png',
  SAR: 'https://media.formula1.com/content/dam/fom-website/drivers/L/LOGSAR01_Logan_Sargeant/logsar01.png',
  LAW: 'https://media.formula1.com/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png',
  BEA: 'https://media.formula1.com/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png',
  COL: 'https://media.formula1.com/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png',
};
