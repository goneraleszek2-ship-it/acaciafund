#!/usr/bin/env node
/**
 * Performance Analysis Script for AcaciaFund
 * Analyzes collected performance data and generates optimization recommendations
 */

import { readFileSync, existsSync, readdirSync, statSync, writeFileSync } from 'fs';
import { join, extname } from 'path';

// Configuration
const CONFIG = {
  // Directory containing performance reports
  reportsDir: './performance-reports',
  
  // Output file for analysis
  outputFile: './performance-analysis.md',
  
  // Thresholds for Core Web Vitals (based on Google's recommendations)
  thresholds: {
    lcp: { good: 2500, needsImprovement: 4000 }, // milliseconds
    cls: { good: 0.1, needsImprovement: 0.25 }, // unitless
    inp: { good: 200, needsImprovement: 500 } // milliseconds
  }
};

/**
 * Classify a metric value based on thresholds
 * @param {number} value - The metric value
 * @param {string} metric - The metric name ('lcp', 'cls', 'inp')
 * @returns {string} - 'good', 'needs-improvement', or 'poor'
 */
function classifyMetric(value, metric) {
  const thresholds = CONFIG.thresholds[metric];
  if (!thresholds) return 'unknown';
  
  if (value <= thresholds.good) return 'good';
  if (value <= thresholds.needsImprovement) return 'needs-improvement';
  return 'poor';
}

/**
 * Analyze performance reports and generate recommendations
 */
function analyzePerformanceReports() {
  if (!existsSync(CONFIG.reportsDir)) {
    console.error(`Reports directory not found: ${CONFIG.reportsDir}`);
    return;
  }
  
  const files = readdirSync(CONFIG.reportsDir)
    .filter(file => extname(file) === '.json')
    .map(file => join(CONFIG.reportsDir, file))
    .sort((a, b) => {
      // Sort by modification time, newest first
      const statA = statSync(a);
      const statB = statSync(b);
      return statB.mtimeMs - statA.mtimeMs;
    });
  
  if (files.length === 0) {
    console.log('No performance reports found.');
    return;
  }
  
  console.log(`Found ${files.length} performance reports.`);
  
  // Parse all reports
  const reports = files.map(file => {
    try {
      const content = readFileSync(file, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error(`Error parsing ${file}:`, error.message);
      return null;
    }
  }).filter(report => report !== null);
  
  if (reports.length === 0) {
    console.log('No valid performance reports found.');
    return;
  }
  
  console.log(`Parsed ${reports.length} valid performance reports.`);
  
  // Analyze the data
  const analysis = {
    timestamp: new Date().toISOString(),
    totalReports: reports.length,
    urlAnalysis: {},
    overallMetrics: {
      lcp: { values: [], classifications: [] },
      cls: { values: [], classifications: [] },
      inp: { values: [], classifications: [] }
    },
    opportunities: {}
  };
  
  // Process each report
  reports.forEach(report => {
    const url = report.url;
    
    // Initialize URL analysis if not present
    if (!analysis.urlAnalysis[url]) {
      analysis.urlAnalysis[url] = {
        lcp: { values: [], classifications: [] },
        cls: { values: [], classifications: [] },
        inp: { values: [], classifications: [] }
      };
    }
    
    // Extract Core Web Vitals
    const vitals = report.coreWebVitals;
    if (vitals) {
      ['lcp', 'cls', 'inp'].forEach(metric => {
        const value = vitals[metric]?.value;
        if (value !== null) {
          analysis.overallMetrics[metric].values.push(value);
          const classification = classifyMetric(value, metric);
          analysis.overallMetrics[metric].classifications.push(classification);
          
          analysis.urlAnalysis[url][metric].values.push(value);
          analysis.urlAnalysis[url][metric].classifications.push(classification);
        }
      });
    }
    
    // Collect opportunities
    if (report.opportunities && Array.isArray(report.opportunities)) {
      report.opportunities.forEach(opp => {
        if (!analysis.opportunities[opp.id]) {
          analysis.opportunities[opp.id] = {
            title: opp.title,
            description: opp.description,
            count: 0,
            totalScore: 0,
            occurrences: []
          };
        }
        
        analysis.opportunities[opp.id].count++;
        analysis.opportunities[opp.id].totalScore += opp.score;
        analysis.opportunities[opp.id].occurrences.push({
          url: url,
          timestamp: report.timestamp,
          score: opp.score,
          numericValue: opp.numericValue,
          displayValue: opp.displayValue
        });
      });
    }
  });
  
  // Calculate summary statistics
  const summary = {
    overall: {},
    byUrl: {},
    topOpportunities: []
  };
  
  // Overall metrics summary
  ['lcp', 'cls', 'inp'].forEach(metric => {
    const values = analysis.overallMetrics[metric].values;
    const classifications = analysis.overallMetrics[metric].classifications;
    
    if (values.length > 0) {
      const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
      const goodCount = classifications.filter(c => c === 'good').length;
      const needsImprovementCount = classifications.filter(c => c === 'needs-improvement').length;
      const poorCount = classifications.filter(c => c === 'poor').length;
      
      summary.overall[metric] = {
        average: avg,
        goodPercentage: (goodCount / values.length) * 100,
        needsImprovementPercentage: (needsImprovementCount / values.length) * 100,
        poorPercentage: (poorCount / values.length) * 100,
        totalSamples: values.length
      };
    }
  });
  
  // Per-URL metrics summary
  Object.keys(analysis.urlAnalysis).forEach(url => {
    summary.byUrl[url] = {};
    ['lcp', 'cls', 'inp'].forEach(metric => {
      const values = analysis.urlAnalysis[url][metric].values;
      const classifications = analysis.urlAnalysis[url][metric].classifications;
      
      if (values.length > 0) {
        const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
        const goodCount = classifications.filter(c => c === 'good').length;
        const needsImprovementCount = classifications.filter(c => c === 'needs-improvement').length;
        const poorCount = classifications.filter(c => c === 'poor').length;
        
        summary.byUrl[url][metric] = {
          average: avg,
          goodPercentage: (goodCount / values.length) * 100,
          needsImprovementPercentage: (needsImprovementCount / values.length) * 100,
          poorPercentage: (poorCount / values.length) * 100,
          totalSamples: values.length
        };
      }
    });
  });
  
  // Top opportunities sorted by frequency and score
  summary.topOpportunities = Object.entries(analysis.opportunities)
    .map(([id, data]) => ({
      id,
      title: data.title,
      description: data.description,
      count: data.count,
      averageScore: data.totalScore / data.count,
      occurrences: data.occurrences
    }))
    .sort((a, b) => {
      // Sort by count (descending), then by average score (ascending - lower score = worse)
      if (a.count !== b.count) return b.count - a.count;
      return a.averageScore - b.averageScore;
    })
    .slice(0, 10); // Top 10
  
  // Generate markdown report
  const markdown = generateMarkdownReport(summary, analysis);
  
  // Write to file
  writeFileSync(CONFIG.outputFile, markdown);
  console.log(`Analysis written to: ${CONFIG.outputFile}`);
  
  // Also print summary to console
  console.log('\n=== PERFORMANCE ANALYSIS SUMMARY ===');
  console.log(`Analyzed ${reports.length} reports from ${Object.keys(summary.byUrl).length} URLs`);
  
  console.log('\n--- Overall Core Web Vitals ---');
  Object.keys(summary.overall).forEach(metric => {
    const data = summary.overall[metric];
    console.log(`${metric.toUpperCase()}: ${data.average.toFixed(0)}ms (Good: ${data.goodPercentage.toFixed(1)}%, NI: ${data.needsImprovementPercentage.toFixed(1)}%, Poor: ${data.poorPercentage.toFixed(1)}%)`);
  });
  
  console.log(`\n--- Top ${summary.topOpportunities.length} Optimization Opportunities ---`);
  summary.topOpportunities.forEach((opp, index) => {
    console.log(`${index + 1}. ${opp.title} (Found ${opp.count} times, Avg Score: ${opp.averageScore.toFixed(2)})`);
  });
}

/**
 * Generate markdown report from analysis data
 * @param {Object} summary - Summary statistics
 * @param {Object} analysis - Full analysis data
 * @returns {string} - Markdown formatted report
 */
function generateMarkdownReport(summary, analysis) {
  let markdown = `# AcaciaFund Performance Analysis\n\n`;
  markdown += `Generated: ${new Date(analysis.timestamp).toLocaleString()}\n\n`;
  markdown += `## Executive Summary\n\n`;
  markdown += `This report analyzes ${analysis.totalReports} performance reports collected from `;
  markdown += `${Object.keys(summary.byUrl).length} unique URLs on the AcaciaFund website.\n\n`;
  
  markdown += `## Overall Core Web Vitals Performance\n\n`;
  markdown += `| Metric | Average | Good (%) | Needs Improvement (%) | Poor (%) |\n`;
  markdown += `|--------|---------|----------|-----------------------|----------|\n`;
  
  ['lcp', 'cls', 'inp'].forEach(metric => {
    const data = summary.overall[metric];
    if (data) {
      let unit = 'ms';
      if (metric === 'cls') unit = '';
      markdown += `| ${metric.toUpperCase()} | ${data.average.toFixed(0)}${unit} | ${data.goodPercentage.toFixed(1)} | ${data.needsImprovementPercentage.toFixed(1)} | ${data.poorPercentage.toFixed(1)} |\n`;
    }
  });
  
  markdown += `\n## Per-URL Performance\n\n`;
  
  Object.keys(summary.byUrl).forEach(url => {
    markdown += `### ${url}\n\n`;
    markdown += `| Metric | Average | Good (%) | Needs Improvement (%) | Poor (%) |\n`;
    markdown += `|--------|---------|----------|-----------------------|----------|\n`;
    
    ['lcp', 'cls', 'inp'].forEach(metric => {
      const data = summary.byUrl[url][metric];
      if (data) {
        let unit = 'ms';
        if (metric === 'cls') unit = '';
        markdown += `| ${metric.toUpperCase()} | ${data.average.toFixed(0)}${unit} | ${data.goodPercentage.toFixed(1)} | ${data.needsImprovementPercentage.toFixed(1)} | ${data.poorPercentage.toFixed(1)} |\n`;
      }
    });
    
    markdown += `\n`;
  });
  
  markdown += `## Top Optimization Opportunities\n\n`;
  markdown += `| Rank | Opportunity | Frequency | Avg Score | Description |\n`;
  markdown += `|------|-------------|-----------|-----------|-------------|\n`;
  
  summary.topOpportunities.forEach((opp, index) => {
    markdown += `| ${index + 1} | ${opp.title} | ${opp.count} | ${opp.averageScore.toFixed(2)} | ${opp.description} |\n`;
  });
  
  markdown += `\n## Recommendations\n\n`;
  
  // Generate recommendations based on analysis
  const recommendations = generateRecommendations(summary);
  recommendations.forEach((rec, index) => {
    markdown += `${index + 1}. ${rec}\n`;
  });
  
  markdown += `\n---\n*Analysis generated by AcaciaFund Performance Monitoring System*\n`;
  
  return markdown;
}

/**
 * Generate optimization recommendations based on analysis
 * @param {Object} summary - Summary statistics
 * @returns {string[]} - Array of recommendation strings
 */
function generateRecommendations(summary) {
  const recommendations = [];
  
  // LCP recommendations
  const lcpData = summary.overall.lcp;
  if (lcpData && lcpData.poorPercentage > 20) {
    recommendations.push(`Optimize Largest Contentful Paint (LCP): ${lcpData.poorPercentage.toFixed(1)}% of page loads have poor LCP (>4000ms). Consider optimizing hero images, implementing proper image sizing with srcset, and preloading critical resources.`);
  } else if (lcpData && lcpData.needsImprovementPercentage > 20) {
    recommendations.push(`Improve Largest Contentful Paint (LCP): ${lcpData.needsImprovementPercentage.toFixed(1)}% of page loads need improvement (2500-4000ms). Optimize server response times and consider using a CDN.`);
  }
  
  // CLS recommendations
  const clsData = summary.overall.cls;
  if (clsData && clsData.poorPercentage > 20) {
    recommendations.push(`Fix Cumulative Layout Shift (CLS): ${clsData.poorPercentage.toFixed(1)}% of page loads have poor CLS (>0.25). Ensure all media elements have explicit width and height attributes, and avoid inserting content above existing content.`);
  } else if (clsData && clsData.needsImprovementPercentage > 20) {
    recommendations.push(`Reduce Cumulative Layout Shift (CLS): ${clsData.needsImprovementPercentage.toFixed(1)}% of page loads need improvement (0.1-0.25). Use CSS aspect-ratio boxes or reserve space for dynamic content.`);
  }
  
  // INP recommendations
  const inpData = summary.overall.inp;
  if (inpData && inpData.poorPercentage > 20) {
    recommendations.push(`Optimize Interaction to Next Paint (INP): ${inpData.poorPercentage.toFixed(1)}% of page loads have poor INP (>500ms). Break up long JavaScript tasks, defer non-critical JavaScript, and consider using web workers for complex computations.`);
  } else if (inpData && inpData.needsImprovementPercentage > 20) {
    recommendations.push(`Improve Interaction to Next Paint (INP): ${inpData.needsImprovementPercentage.toFixed(1)}% of page loads need improvement (200-500ms). Minimize main-thread work and optimize event handlers.`);
  }
  
  // Add recommendations based on top opportunities
  if (summary.topOpportunities.length > 0) {
    const topOpp = summary.topOpportunities[0];
    recommendations.push(`Address top recurring issue: "${topOpp.title}" (found ${topOpp.count} times). This opportunity has an average score of ${topOpp.averageScore.toFixed(2)}, indicating significant room for improvement.`);
  }
  
  // General recommendations if no specific issues found
  if (recommendations.length === 0) {
    recommendations.push(`Core Web Vitals are performing well across the site. Continue monitoring and consider implementing advanced optimizations like CSS containment, font loading strategies, and advanced image formats (AVIF).`);
    recommendations.push(`Consider setting up performance budgets in your CI/CD pipeline to prevent regressions.`);
  }
  
  return recommendations;
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  analyzePerformanceReports().catch(console.error);
}

export { analyzePerformanceReports };