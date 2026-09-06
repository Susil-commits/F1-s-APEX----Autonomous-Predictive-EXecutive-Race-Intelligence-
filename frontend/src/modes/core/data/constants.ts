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
  { code: 'NOR', firstName: 'Lando', lastName: 'NORRIS', team: 'McLaren', number: 4, color: '#FF8000', country: '🇬🇧', defaultGrid: 2, photo: '/f1/drivers/NOR.png' },
  { code: 'VER', firstName: 'Max', lastName: 'VERSTAPPEN', team: 'Red Bull Racing', number: 1, color: '#3671C6', country: '🇳🇱', defaultGrid: 1, photo: '/f1/drivers/VER.png' },
  { code: 'LEC', firstName: 'Charles', lastName: 'LECLERC', team: 'Ferrari', number: 16, color: '#E80020', country: '🇲🇨', defaultGrid: 3, photo: '/f1/drivers/LEC.png' },
  { code: 'HAM', firstName: 'Lewis', lastName: 'HAMILTON', team: 'Ferrari', number: 44, color: '#E80020', country: '🇬🇧', defaultGrid: 5, photo: '/f1/drivers/HAM.png' },
  { code: 'RUS', firstName: 'George', lastName: 'RUSSELL', team: 'Mercedes', number: 63, color: '#00A19B', country: '🇬🇧', defaultGrid: 6, photo: '/f1/drivers/RUS.png' },
  { code: 'ANT', firstName: 'Kimi', lastName: 'ANTONELLI', team: 'Mercedes', number: 12, color: '#00A19B', country: '🇮🇹', defaultGrid: 7, photo: '/f1/drivers/ANT.png' },
  { code: 'PIA', firstName: 'Oscar', lastName: 'PIASTRI', team: 'McLaren', number: 81, color: '#FF8000', country: '🇦🇺', defaultGrid: 4, photo: '/f1/drivers/PIA.png' },
  { code: 'SAI', firstName: 'Carlos', lastName: 'SAINZ', team: 'Williams', number: 55, color: '#64C4FF', country: '🇪🇸', defaultGrid: 8, photo: '/f1/drivers/SAI.png' },
  { code: 'ALO', firstName: 'Fernando', lastName: 'ALONSO', team: 'Aston Martin', number: 14, color: '#229971', country: '🇪🇸', defaultGrid: 9, photo: '/f1/drivers/ALO.png' },
  { code: 'ALB', firstName: 'Alexander', lastName: 'ALBON', team: 'Williams', number: 23, color: '#64C4FF', country: '🇹🇭', defaultGrid: 12, photo: '/f1/drivers/ALB.png' },
  { code: 'TSU', firstName: 'Yuki', lastName: 'TSUNODA', team: 'RB', number: 22, color: '#6692FF', country: '🇯🇵', defaultGrid: 11, photo: '/f1/drivers/TSU.png' },
  { code: 'HUL', firstName: 'Nico', lastName: 'HULKENBERG', team: 'Kick Sauber', number: 27, color: '#52E252', country: '🇩🇪', defaultGrid: 13, photo: '/f1/drivers/HUL.png' },
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
