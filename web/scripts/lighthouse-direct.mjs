#!/usr/bin/env node
/**
 * Performance Monitoring Script for AcaciaFund
 * Uses Lighthouse Node.js API directly to collect lab metrics
 * Can be run via npm script or CI/CD pipeline
 */

import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

// Configuration
const CONFIG = {
  // Target URLs to test
  urls: [
    'https://acaciafund.pages.dev/',
    'https://acaciafund.pages.dev/learn/',
    'https://acaciafund.pages.dev/blog/'
  ],
  
  // Output directory for reports
  outputDir: './lighthouse-reports',
  
  // Test strategy: 'mobile' or 'desktop'
  strategy: 'mobile',
  
  // Only generate performance report for faster execution
  onlyCategories: ['performance'],
  
  // Chrome flags for Lighthouse - let Lighthouse handle Chrome instance
  chromeFlags: []
};

// Create output directory if it doesn't exist
if (!existsSync(CONFIG.outputDir)) {
  mkdirSync(CONFIG.outputDir, { recursive: true });
}

/**
 * Launch Chrome and run Lighthouse
 * @param {string} url - URL to test
 * @param {Object} options - Lighthouse options
 * @returns {Promise<Object>} - Lighthouse results
 */
async function runLighthouse(url, options = {}) {
  const chrome = await chromeLauncher.launch({ 
    chromeFlags: CONFIG.chromeFlags 
  });
  
  options.port = chrome.port;
  
  try {
    const runnerResult = await lighthouse(url, {
      ...options,
      port: chrome.port
    });
    
    // `.report` is the HTML report as a string
    // `.lhr` is the LHR (Lighthouse Result) as a JSON object
    return { 
      lhr: runnerResult.lhr,
      report: runnerResult.report 
    };
  } finally {
    await chrome.kill();
  }
}

/**
 * Extract Core Web Vitals from Lighthouse response
 * Note: Lighthouse provides lab metrics, not field data
 * @param {Object} lhr - Lighthouse Result
 * @returns {Object} - Core Web Vitals metrics (lab values)
 */
function extractCoreWebVitals(lhr) {
  const audits = lhr.audits || {};
  
  return {
    // LCP: Largest Contentful Paint
    lcp: {
      value: audits['largest-contentful-paint']?.numericValue || null,
      unit: 'milliseconds',
      rating: audits['largest-contentful-paint']?.score !== null 
        ? audits['largest-contentful-paint'].score >= 0.9 
          ? 'good' 
          : audits['largest-contentful-paint'].score >= 0.5 
            ? 'needs-improvement' 
            : 'poor'
        : null
    },
    
    // CLS: Cumulative Layout Shift
    cls: {
      value: audits['cumulative-layout-shift']?.numericValue || null,
      unit: 'hundredths',
      rating: audits['cumulative-layout-shift']?.score !== null 
        ? audits['cumulative-layout-shift'].score >= 0.1 
          ? 'good' 
          : audits['cumulative-layout-shift'].score >= 0.25 
            ? 'needs-improvement' 
            : 'poor'
        : null
    },
    
    // TBT: Total Blocking Time (proxy for INP/FID in lab)
    tbt: {
      value: audits['total-blocking-time']?.numericValue || null,
      unit: 'milliseconds',
      rating: audits['total-blocking-time']?.score !== null 
        ? audits['total-blocking-time'].score >= 0.75 
          ? 'good' 
          : audits['total-blocking-time'].score >= 0.5 
            ? 'needs-improvement' 
            : 'poor'
        : null
    }
  };
}

/**
 * Generate performance report
 * @param {Object} lhr - Lighthouse Result
 * @param {string} url - Tested URL
 * @returns {Object} - Formatted report
 */
function generateReport(lhr, url) {
  const coreWebVitals = extractCoreWebVitals(lhr);
  
  return {
    url: url,
    timestamp: new Date().toISOString(),
    strategy: CONFIG.strategy,
    coreWebVitals: coreWebVitals,
    performanceScore: lhr.categories?.performance?.score * 100 || null,
    // Additional metrics
    metrics: {
      firstContentfulPaint: lhr.audits?.first-contentful-paint?.numericValue || null,
      speedIndex: lhr.audits?.speed-index?.numericValue || null,
      largestContentfulPaint: lhr.audits?.largest-contentful-paint?.numericValue || null,
      interactive: lhr.audits?.interactive?.numericValue || null,
      totalBlockingTime: lhr.audits?.total-blocking-time?.numericValue || null,
      cumulativeLayoutShift: lhr.audits?.cumulative-layout-shift?.numericValue || null
    },
    // Opportunities for improvement
    opportunities: lhr.categories?.performance?.auditRefs
      ?.filter(ref => lhr.audits?.[ref.id]?.score < 0.9)
      .map(ref => ({
        id: ref.id,
        title: lhr.audits?.[ref.id]?.title || '',
        description: lhr.audits?.[ref.id]?.description || '',
        score: lhr.audits?.[ref.id]?.score || 0,
        numericValue: lhr.audits?.[ref.id]?.numericValue || null,
        displayValue: lhr.audits?.[ref.id]?.displayValue || ''
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
  
  console.log('\n--- Core Web Vitals (Lab) ---');
  const vitals = report.coreWebVitals;
  console.log(`LCP: ${vitals.lcp.value !== null ? vitals.lcp.value.toFixed(0) + ' ' + vitals.lcp.unit : 'N/A'} (${vitals.lcp.rating || 'unknown'})`);
  console.log(`CLS: ${vitals.cls.value !== null ? vitals.cls.value.toFixed(3) + ' ' + vitals.cls.unit : 'N/A'} (${vitals.cls.rating || 'unknown'})`);
  console.log(`TBT: ${vitals.tbt.value !== null ? vitals.tbt.value.toFixed(0) + ' ' + vitals.tbt.unit : 'N/A'} (${vitals.tbt.rating || 'unknown'})`);
  
  console.log(`\n--- Performance Score ---`);
  console.log(`Score: ${report.performanceScore !== null ? report.performanceScore.toFixed(1) + '%' : 'N/A'}`);
  
  console.log(`\n--- Metrics ---`);
  const metrics = report.metrics;
  console.log(`FCP: ${metrics.firstContentfulPaint !== null ? metrics.firstContentfulPaint.toFixed(0) + 'ms' : 'N/A'}`);
  console.log(`SI: ${metrics.speedIndex !== null ? metrics.speedIndex.toFixed(0) + 'ms' : 'N/A'}`);
  console.log(`LCP: ${metrics.largestContentfulPaint !== null ? metrics.largestContentfulPaint.toFixed(0) + 'ms' : 'N/A'}`);
  console.log(`TTI: ${metrics.interactive !== null ? metrics.interactive.toFixed(0) + 'ms' : 'N/A'}`);
  console.log(`TBT: ${metrics.totalBlockingTime !== null ? metrics.totalBlockingTime.toFixed(0) + 'ms' : 'N/A'}`);
  console.log(`CLS: ${metrics.cumulativeLayoutShift !== null ? metrics.cumulativeLayoutShift.toFixed(3) : 'N/A'}`);
  
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
 * Main function to run Lighthouse audits
 */
async function runLighthouseAudit() {
  console.log('Starting Lighthouse Performance Audit (Direct API)...');
  console.log(`Testing ${CONFIG.urls.length} URLs with ${CONFIG.strategy} strategy`);
  
  const results = [];
  
  for (const url of CONFIG.urls) {
    try {
      console.log(`\nTesting: ${url}`);
      const lighthouseResult = await runLighthouse(url, {
        onlyCategories: CONFIG.onlyCategories,
        // Emulate mobile device
        emulatedFormFactor: CONFIG.strategy === 'mobile' ? 'mobile' : 'desktop'
      });
      
      const report = generateReport(lighthouseResult.lhr, url);
      
      saveReport(report, url);
      printSummary(report);
      
      results.push(report);
      
      // Small delay between tests
      if (url !== CONFIG.urls[CONFIG.urls.length - 1]) {
        console.log('Waiting 5 seconds before next test...');
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    } catch (error) {
      console.error(`Failed to test ${url}:`, error.message);
      results.push({
        url: url,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
  
  // Save summary report
  const summary = {
    timestamp: new Date().toISOString(),
    strategy: CONFIG.strategy,
    results: results
  };
  
  const summaryPath = join(CONFIG.outputDir, `summary-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  console.log(`\nSummary saved: ${summaryPath}`);
  
  console.log('\n=== Audit Complete ===');
  return results;
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runLighthouseAudit().catch(console.error);
}

export { runLighthouseAudit, runLighthouse, generateReport };