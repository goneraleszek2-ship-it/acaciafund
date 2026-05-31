import type { APIRoute } from 'astro';

// In-memory storage for performance data (in production, use a proper database)
let performanceData: any[] = [];

export const POST: APIRoute = async ({ request }) => {
  try {
    const data = await request.json();
    
    // Validate required fields
    if (!data.url || !data.timestamp) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400 }
      );
    }
    
    // Store the data
    performanceData.push({
      ...data,
      receivedAt: new Date().toISOString()
    });
    
    // Keep only last 1000 entries to prevent memory issues
    if (performanceData.length > 1000) {
      performanceData = performanceData.slice(-1000);
    }
    
    console.log(`Received performance data for ${data.url}:`, {
      lcp: data.lcp?.value,
      cls: data.cls?.value,
      inp: data.inp?.value
    });
    
    return new Response(
      JSON.stringify({ status: 'ok', stored: performanceData.length }),
      { status: 200 }
    );
  } catch (error) {
    console.error('Error processing performance data:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500 }
    );
  }
};

export const GET: APIRoute = async () => {
  // Return summary statistics
  const summary = {
    totalSamples: performanceData.length,
    lastUpdated: new Date().toISOString(),
    // Calculate averages for core web vitals
    averages: {
      lcp: calculateAverage(performanceData, 'lcp.value'),
      cls: calculateAverage(performanceData, 'cls.value'),
      inp: calculateAverage(performanceData, 'inp.value')
    },
    // Percentage of good scores
    goodScores: {
      lcp: calculateGoodPercentage(performanceData, 'lcp.value', 2500), // < 2.5s is good
      cls: calculateGoodPercentage(performanceData, 'cls.value', 0.1), // < 0.1 is good
      inp: calculateGoodPercentage(performanceData, 'inp.value', 200) // < 200ms is good
    }
  };
  
  return new Response(
    JSON.stringify(summary),
    { status: 200 }
  );
};

// Helper function to calculate average of a nested property
function calculateAverage(data: any[], path: string): number | null {
  const values = data
    .map(item => {
      const keys = path.split('.');
      let value = item;
      for (const key of keys) {
        if (value === null || value === undefined || !(key in value)) {
          return null;
        }
        value = value[key];
      }
      return typeof value === 'number' ? value : null;
    })
    .filter((val): val is number => val !== null);
  
  if (values.length === 0) return null;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

// Helper function to calculate percentage of values below threshold
function calculateGoodPercentage(data: any[], path: string, threshold: number): number {
  const values = data
    .map(item => {
      const keys = path.split('.');
      let value = item;
      for (const key of keys) {
        if (value === null || value === undefined || !(key in value)) {
          return null;
        }
        value = value[key];
      }
      return typeof value === 'number' ? value : null;
    })
    .filter((val): val is number => val !== null);
  
  if (values.length === 0) return 0;
  const goodValues = values.filter(val => val <= threshold);
  return (goodValues.length / values.length) * 100;
}