export function nextPinPosition(tokens: Array<{ latitude: number; longitude: number }>) {
  for (const latitude of [50, 42, 58, 34, 66, 26, 74, 18, 82, 10, 90]) {
    for (const longitude of [50, 42, 58, 34, 66, 26, 74, 18, 82, 10, 90]) {
      if (!tokens.some(t => Math.abs(t.latitude - latitude) < 5 && Math.abs(t.longitude - longitude) < 5)) return { latitude, longitude };
    }
  }
  return { latitude: 50, longitude: 50 };
}
