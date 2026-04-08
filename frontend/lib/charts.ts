// frontend/lib/charts.ts
// Centralized chart URL builder — matches backend static file mount

export function getChartUrl(userId: number, clientName: string, chartFile: string): string {
  const safe = clientName.toLowerCase().replace(/ /g, "_");
  // Backend mounts /static → data/
  // So chart path is: /static/users/{userId}/{clientName}/charts/{chart}
  return `http://localhost:8000/static/users/${userId}/${safe}/charts/${chartFile}`;
}
