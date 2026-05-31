#!/usr/bin/env node
/**
 * Performance Monitoring Script for AcaciaFund
 * Uses PageSpeed Insights API to collect lab metrics
 * Testing a single URL to establish baseline
 */

import fetch from 'node-fetch';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

// Configuration
const CONFIG = {
  // Single URL to test (homepage)
  url: 'https://acaciafund.pages.dev/',
  
  // PageSpeed Insights API endpoint
  psiUrl: 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed',
  
  // Optional: API key for higher rate limits (get from https://developers.google.com/speed/docs/insights/v5/get-started)
  // Leave empty to use free tier (limited requests per day)
  apiKey: process.env.PAGESPEED_API_KEY || '',
  
  // Output directory for reports
  outputDir: './performance-reports',
  
  // Test strategy: 'mobile' or 'desktop'
  strategy: 'mobile',
  
  // Categories to test
  categories: ['performance', 'accessibility', 'best-practices', 'seo'],
  
  // Retry configuration
  maxRetries: 2,
  baseDelay: 60000, // 60 seconds base delay
  maxDelay: 300000  // 5 minutes max delay
};

// Create output directory if it doesn't exist
if (!existsSync(CONFIG.outputDir)) {
  mkdirSync(CONFIG.outputDir, { recursive: true });
}

/**
 * Fetch data from PageSpeed Insights API with retry logic
 * @param {string} url - URL to test
 * @returns {Promise<Object>} - PSI response data
 */
async function fetchPageSpeedData(url) {
  const params = new URLSearchParams({
    url: url,
    strategy: CONFIG.strategy,
    categories: CONFIG.categories.join(',')
  });
  
  if (CONFIG.apiKey) {
    params.append('key', CONFIG.apiKey);
  }
  
  const apiUrl = `${CONFIG.psiUrl}?${params.toString()}`;
  
  let lastError;
  
  for (let attempt = 0; attempt <= CONFIG.maxRetries; attempt++) {
    try {
      const response = await fetch(apiUrl);
      
      if (response.ok) {
        return await response.json();
      }
      
      // Handle rate limiting specifically
      if (response.status === 429) {
        const retryAfter = response.headers.get('retry-after');
        const delay = retryAfter 
          ? parseInt(retryAfter) * 1000 
          : Math.min(CONFIG.baseDelay * Math.pow(2, attempt) + Math.random() * 1000, CONFIG.maxDelay);
        
        console.log(`Rate limited for ${url}. Waiting ${delay/1000} seconds before retry ${attempt + 1}/${CONFIG.maxRetries}...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        lastError = new Error(`PSI API rate limit: ${response.status} ${response.statusText}`);
        continue;
      }
      
      // For other errors, don't retry
      throw new Error(`PSI API error: ${response.status} ${response.statusText}`);
    } catch (error) {
      lastError = error;
      
      // If this was the last attempt, throw the error
      if (attempt === CONFIG.maxRetries) {
        break;
      }
      
      // For non-rate-limit errors, wait briefly before retrying
      if (error.message && !error.message.includes('rate limit')) {
        const delay = Math.min(CONFIG.baseDelay * Math.pow(2, attempt) + Math.random() * 1000, CONFIG.maxDelay);
        console.log(`Error fetching PSI data for ${url}: ${error.message}. Retrying in ${delay/1000} seconds...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

/**
 * Extract Core Web Vitals from PSI response
 * @param {Object} psiData - PageSpeed Insights response
 * @returns {Object} - Core Web Vitals metrics
 */
function extractCoreWebVitals(psiData) {
  const loadingExperience = psiData.loadingExperience || {};
  const metrics = loadingExperience.metrics || {};
  
  return {
    // LCP: Largest Contentful Paint
    lcp: {
      value: metrics.LCP ? metrics.LCP.percentile : null,
      unit: 'milliseconds',
      rating: metrics.LCP ? metrics.LCP.category : null
    },
    
    // CLS: Cumulative Layout Shift
    cls: {
      value: metrics.CLS ? metrics.CLS.percentile : null,
      unit: 'hundredths',
      rating: metrics.CLS ? metrics.CLS.category : null
    },
    
    // INP: Interaction to Next Paint (replaced FID)
    inp: {
      value: metrics.INP ? metrics.INP.percentile : null,
      unit: 'milliseconds',
      rating: metrics.INP ? metrics.INP.category : null
    }
  };
}

/**
 * Generate performance report
 * @param {Object} psiData - PageSpeed Insights response
 * @param {string} url - Tested URL
 * @returns {Object} - Formatted report
 */
function generateReport(psiData, url) {
  const lighthouseResult = psiData.lighthouseResult || {};
  const coreWebVitals = extractCoreWebVitals(psiData);
  
  return {
    url: url,
    timestamp: new Date().toISOString(),
    strategy: CONFIG.strategy,
    coreWebVitals: coreWebVitals,
    lighthouseScores: {
      performance: lighthouseResult.categories?.performance?.score * 100 || null,
      accessibility: lighthouseResult.categories?.accessibility?.score * 100 || null,
      'best-practices': lighthouseResult.categories?.['best-practices']?.score * 100 || null,
      seo: lighthouseResult.categories?.seo?.score * 100 || null
    },
    // Additional diagnostics
    diagnostics: {
      totalBlockingTime: lighthouseResult.audits?.total-blocking-time?.numericValue || null,
      firstContentfulPaint: lighthouseResult.audits?.first-contentful-paint?.numericValue || null,
      speedIndex: lighthouseResult.audits?.speed-index?.numericValue || null,
      largestContentfulPaint: lighthouseResult.audits?.largest-contentful-paint?.numericValue || null,
      cumulativeLayoutShift: lighthouseResult.audits?.cumulative-layout-shift?.numericValue || null
    },
    // Opportunities for improvement
    opportunities: lighthouseResult.categories?.performance?.auditRefs
      ?.filter(ref => lighthouseResult.audits?.[ref.id]?.score < 0.9)
      .map(ref => ({
        id: ref.id,
        title: lighthouseResult.audits?.[ref.id]?.title || '',
        description: lighthouseResult.audits?.[ref.id]?.description || '',
        score: lighthouseResult.audits?.[ref.id]?.score || 0,
        numericValue: lighthouseResult.audits?.[ref.id]?.numericValue || null,
        displayValue: lighthouseResult.audits?.[ref.id]?.displayValue || ''
      })) || []
  };
}

/**
 * Save report to file
 * @param {Object} report - Performance report
 * @param {string} url - Tested URL
 */
function saveReport(report, url) {
  // Create filename from URL and timestamp
  const urlObj = new URL(url);
  const hostname = urlObj.hostname.replace('.', '-');
  const pathname = urlObj.pathname.replace(/\//g, '-').replace(/^-|-$/g, '') || 'home';
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  const filename = `${hostname}-${pathname}-${timestamp}.json`;
  const filepath = join(CONFIG.outputDir, filename);
  
  writeFileSync(filepath, JSON.stringify(report, null, 2));
  console.log(`Report saved: ${filepath}`);
}

/**
 * Print summary to console
 * @param {Object} report - Performance report
 */
function printSummary(report) {
  console.log(`\n=== Performance Report for ${report.url} ===`);
  console.log(`Time: ${new Date(report.timestamp).toLocaleString()}`);
  console.log(`Strategy: ${report.strategy}`);
  
  console.log('\n--- Core Web Vitals ---');
  const vitals = report.coreWebVitals;
  console.log(`LCP: ${vitals.lcp.value !== null ? vitals.lcp.value + ' ' + vitals.lcp.unit : 'N/A'} (${vitals.lcp.rating || 'unknown'})`);
  console.log(`CLS: ${vitals.cls.value !== null ? vitals.cls.value + ' ' + vitals.cls.unit : 'N/A'} (${vitals.cls.rating || 'unknown'})`);
  console.log(`INP: ${vitals.inp.value !== null ? vitals.inp.value + ' ' + vitals.inp.unit : 'N/A'} (${vitals.inp.rating || 'unknown'})`);
  
  console.log('\n--- Lighthouse Scores ---');
  const scores = report.lighthouseScores;
  console.log(`Performance: ${scores.performance !== null ? scores.percentage.toFixed(1) + '%' : 'N/A'}`);
  console.log(`Accessibility: ${scores.accessibility !== null ? scores.accessibility.toFixed(1) + '%' : 'N/A'}`);
  console.log(`Best Practices: ${scores['best-practices'] !== null ? scores['best-practices'].toFixed(1) + '%' : 'N/A'}`);
  console.log(`SEO: ${scores.seo !== null ? scores.seo.toFixed(1) + '%' : 'N/A'}`);
  
  console.log(`\n--- Top Opportunities (${report.opportunities.length}) ---`);
  report.opportunities.slice(0, 5).forEach((opp, index) => {
    console.log(`${index + 1}. ${opp.title}`);
    if (opp.description) {
      console.log(`   ${opp.description}`);
    }
  });
  
  if (report.opportunities.length > 5) {
    console.log(`   ... and ${report.opportunities.length - 5} more opportunities`);
  }
}

/**
 * Main function to run performance audit
 */
async function runPerformanceAudit() {
  console.log('Starting Performance Audit (Single URL)...');
  console.log(`Testing: ${CONFIG.url}`);
  if (CONFIG.apiKey) {
    console.log('Using PageSpeed Insights API key');
  } else {
    console.log('Using free tier (rate limited)');
  }
  
  try {
    console.log(`\nTesting: ${CONFIG.url}`);
    const psiData = await fetchPageSpeedData(CONFIG.url);
    const report = generateReport(psiData, CONFIG.url);
    
    saveReport(report, CONFIG.url);
    printSummary(report);
    
    console.log('\n=== Audit Complete ===');
    return report;
  } catch (error) {
    console.error(`Failed to test ${CONFIG.url}:`, error.message);
    throw error;
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runPerformanceAudit().catch(console.error);
}

export { runPerformanceAudit, fetchPageSpeedData, generateReport };