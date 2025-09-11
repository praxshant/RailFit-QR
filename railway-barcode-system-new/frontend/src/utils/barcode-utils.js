export function isRailwayQR(text){ return text && text.startsWith('RW:'); }
export function parseMediaRef(text){ return isRailwayQR(text) ? text.substring(3) : null; }
