#!/usr/bin/env node

/**
 * Bundle Size Analyzer
 * Analyzes and optimizes frontend bundle size
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('📊 Starting Bundle Size Analysis...\n');

// Bundle analysis configuration
const analysisConfig = {
  thresholds: {
    totalSize: 2.5 * 1024 * 1024, // 2.5MB
    jsSize: 1.5 * 1024 * 1024,    // 1.5MB
    cssSize: 200 * 1024,          // 200KB
    imageSize: 500 * 1024,        // 500KB
    fontSize: 100 * 1024          // 100KB
  },
  optimization: {
    enableTreeShaking: true,
    enableMinification: true,
    enableCompression: true,
    enableCodeSplitting: true,
    enableLazyLoading: true
  }
};

// Analyze bundle size
function analyzeBundleSize() {
  console.log('🔍 Analyzing bundle size...');
  
  const buildDir = path.join(__dirname, '..', 'build');
  const staticDir = path.join(buildDir, 'static');
  
  if (!fs.existsSync(buildDir)) {
    console.log('❌ Build directory not found. Run "npm run build" first.');
    return;
  }
  
  const analysis = {
    totalSize: 0,
    jsFiles: [],
    cssFiles: [],
    imageFiles: [],
    fontFiles: [],
    otherFiles: [],
    recommendations: []
  };
  
  // Analyze static files
  if (fs.existsSync(staticDir)) {
    const staticFiles = fs.readdirSync(staticDir, { recursive: true });
    
    staticFiles.forEach(file => {
      const filePath = path.join(staticDir, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isFile()) {
        const size = stats.size;
        const ext = path.extname(file).toLowerCase();
        
        analysis.totalSize += size;
        
        if (ext === '.js') {
          analysis.jsFiles.push({ name: file, size });
        } else if (ext === '.css') {
          analysis.cssFiles.push({ name: file, size });
        } else if (['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'].includes(ext)) {
          analysis.imageFiles.push({ name: file, size });
        } else if (['.woff', '.woff2', '.ttf', '.eot'].includes(ext)) {
          analysis.fontFiles.push({ name: file, size });
        } else {
          analysis.otherFiles.push({ name: file, size });
        }
      }
    });
  }
  
  // Generate recommendations
  generateRecommendations(analysis);
  
  return analysis;
}

// Generate optimization recommendations
function generateRecommendations(analysis) {
  console.log('💡 Generating optimization recommendations...');
  
  const recommendations = [];
  
  // Check total size
  if (analysis.totalSize > analysisConfig.thresholds.totalSize) {
    recommendations.push({
      type: 'warning',
      message: `Total bundle size (${formatBytes(analysis.totalSize)}) exceeds threshold (${formatBytes(analysisConfig.thresholds.totalSize)})`,
      action: 'Consider code splitting and lazy loading'
    });
  }
  
  // Check JS size
  const totalJsSize = analysis.jsFiles.reduce((sum, file) => sum + file.size, 0);
  if (totalJsSize > analysisConfig.thresholds.jsSize) {
    recommendations.push({
      type: 'warning',
      message: `JavaScript bundle size (${formatBytes(totalJsSize)}) exceeds threshold (${formatBytes(analysisConfig.thresholds.jsSize)})`,
      action: 'Enable tree shaking and remove unused code'
    });
  }
  
  // Check CSS size
  const totalCssSize = analysis.cssFiles.reduce((sum, file) => sum + file.size, 0);
  if (totalCssSize > analysisConfig.thresholds.cssSize) {
    recommendations.push({
      type: 'warning',
      message: `CSS bundle size (${formatBytes(totalCssSize)}) exceeds threshold (${formatBytes(analysisConfig.thresholds.cssSize)})`,
      action: 'Remove unused CSS and enable CSS minification'
    });
  }
  
  // Check for large files
  const allFiles = [...analysis.jsFiles, ...analysis.cssFiles, ...analysis.imageFiles, ...analysis.fontFiles];
  const largeFiles = allFiles.filter(file => file.size > 100 * 1024); // 100KB
  
  if (largeFiles.length > 0) {
    recommendations.push({
      type: 'info',
      message: `Found ${largeFiles.length} files larger than 100KB`,
      action: 'Consider optimizing these files',
      files: largeFiles.map(f => `${f.name} (${formatBytes(f.size)})`)
    });
  }
  
  // Check for duplicate dependencies
  const duplicateRecommendations = checkForDuplicates();
  recommendations.push(...duplicateRecommendations);
  
  analysis.recommendations = recommendations;
}

// Check for duplicate dependencies
function checkForDuplicates() {
  const recommendations = [];
  
  try {
    // Analyze package-lock.json for duplicates
    const packageLockPath = path.join(__dirname, '..', 'package-lock.json');
    if (fs.existsSync(packageLockPath)) {
      const packageLock = JSON.parse(fs.readFileSync(packageLockPath, 'utf8'));
      
      // Check for duplicate React versions
      const reactVersions = new Set();
      const reactPackages = [];
      
      function checkDependencies(deps) {
        if (!deps) return;
        
        Object.entries(deps).forEach(([name, info]) => {
          if (name.includes('react')) {
            reactVersions.add(info.version);
            reactPackages.push({ name, version: info.version });
          }
          
          if (info.dependencies) {
            checkDependencies(info.dependencies);
          }
        });
      }
      
      checkDependencies(packageLock.dependencies);
      
      if (reactVersions.size > 1) {
        recommendations.push({
          type: 'warning',
          message: `Found ${reactVersions.size} different React versions`,
          action: 'Consolidate React versions to reduce bundle size',
          versions: Array.from(reactVersions)
        });
      }
    }
  } catch (error) {
    console.log('⚠️ Could not analyze package-lock.json:', error.message);
  }
  
  return recommendations;
}

// Format bytes to human readable format
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Generate optimization report
function generateOptimizationReport(analysis) {
  console.log('📋 Generating optimization report...');
  
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalSize: analysis.totalSize,
      totalSizeFormatted: formatBytes(analysis.totalSize),
      jsFiles: analysis.jsFiles.length,
      cssFiles: analysis.cssFiles.length,
      imageFiles: analysis.imageFiles.length,
      fontFiles: analysis.fontFiles.length,
      otherFiles: analysis.otherFiles.length
    },
    breakdown: {
      javascript: {
        files: analysis.jsFiles,
        totalSize: analysis.jsFiles.reduce((sum, file) => sum + file.size, 0),
        largestFile: analysis.jsFiles.reduce((max, file) => file.size > max.size ? file : max, { size: 0 })
      },
      css: {
        files: analysis.cssFiles,
        totalSize: analysis.cssFiles.reduce((sum, file) => sum + file.size, 0),
        largestFile: analysis.cssFiles.reduce((max, file) => file.size > max.size ? file : max, { size: 0 })
      },
      images: {
        files: analysis.imageFiles,
        totalSize: analysis.imageFiles.reduce((sum, file) => sum + file.size, 0),
        largestFile: analysis.imageFiles.reduce((max, file) => file.size > max.size ? file : max, { size: 0 })
      },
      fonts: {
        files: analysis.fontFiles,
        totalSize: analysis.fontFiles.reduce((sum, file) => sum + file.size, 0),
        largestFile: analysis.fontFiles.reduce((max, file) => file.size > max.size ? file : max, { size: 0 })
      }
    },
    recommendations: analysis.recommendations,
    optimization: {
      treeShaking: analysisConfig.optimization.enableTreeShaking,
      minification: analysisConfig.optimization.enableMinification,
      compression: analysisConfig.optimization.enableCompression,
      codeSplitting: analysisConfig.optimization.enableCodeSplitting,
      lazyLoading: analysisConfig.optimization.enableLazyLoading
    }
  };
  
  // Write report to file
  const reportPath = path.join(__dirname, '..', 'bundle-analysis-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`✅ Optimization report generated: ${reportPath}`);
  
  return report;
}

// Display analysis results
function displayResults(analysis) {
  console.log('\n📊 Bundle Analysis Results:');
  console.log('='.repeat(50));
  
  console.log(`Total Bundle Size: ${formatBytes(analysis.totalSize)}`);
  console.log(`JavaScript Files: ${analysis.jsFiles.length} (${formatBytes(analysis.jsFiles.reduce((sum, file) => sum + file.size, 0))})`);
  console.log(`CSS Files: ${analysis.cssFiles.length} (${formatBytes(analysis.cssFiles.reduce((sum, file) => sum + file.size, 0))})`);
  console.log(`Image Files: ${analysis.imageFiles.length} (${formatBytes(analysis.imageFiles.reduce((sum, file) => sum + file.size, 0))})`);
  console.log(`Font Files: ${analysis.fontFiles.length} (${formatBytes(analysis.fontFiles.reduce((sum, file) => sum + file.size, 0))})`);
  console.log(`Other Files: ${analysis.otherFiles.length} (${formatBytes(analysis.otherFiles.reduce((sum, file) => sum + file.size, 0))})`);
  
  console.log('\n💡 Recommendations:');
  console.log('='.repeat(50));
  
  analysis.recommendations.forEach((rec, index) => {
    const icon = rec.type === 'warning' ? '⚠️' : rec.type === 'error' ? '❌' : 'ℹ️';
    console.log(`${index + 1}. ${icon} ${rec.message}`);
    console.log(`   Action: ${rec.action}`);
    
    if (rec.files) {
      console.log('   Files:');
      rec.files.forEach(file => console.log(`     - ${file}`));
    }
    
    if (rec.versions) {
      console.log('   Versions:');
      rec.versions.forEach(version => console.log(`     - ${version}`));
    }
    
    console.log('');
  });
}

// Apply optimizations
function applyOptimizations() {
  console.log('🔧 Applying optimizations...');
  
  const optimizations = [
    {
      name: 'Enable Tree Shaking',
      command: 'npm run build -- --analyze',
      description: 'Remove unused code from bundle'
    },
    {
      name: 'Enable Code Splitting',
      command: 'npm run build -- --split-chunks',
      description: 'Split code into smaller chunks'
    },
    {
      name: 'Enable Compression',
      command: 'npm run build -- --compress',
      description: 'Compress bundle files'
    }
  ];
  
  optimizations.forEach(opt => {
    console.log(`  Applying: ${opt.name}`);
    console.log(`  Description: ${opt.description}`);
    
    try {
      execSync(opt.command, { stdio: 'pipe' });
      console.log(`  ✅ ${opt.name} applied successfully`);
    } catch (error) {
      console.log(`  ❌ ${opt.name} failed: ${error.message}`);
    }
  });
}

// Main analysis function
function runBundleAnalysis() {
  try {
    const analysis = analyzeBundleSize();
    const report = generateOptimizationReport(analysis);
    displayResults(analysis);
    
    // Apply optimizations if needed
    if (analysis.recommendations.some(rec => rec.type === 'warning' || rec.type === 'error')) {
      console.log('\n🔧 Applying automatic optimizations...');
      applyOptimizations();
    }
    
    console.log('\n🎉 Bundle analysis completed!');
    console.log(`📊 Total bundle size: ${formatBytes(analysis.totalSize)}`);
    console.log(`💡 Recommendations: ${analysis.recommendations.length}`);
    
  } catch (error) {
    console.error('❌ Bundle analysis failed:', error.message);
    process.exit(1);
  }
}

// Run analysis if this script is executed directly
if (require.main === module) {
  runBundleAnalysis();
}

module.exports = {
  analyzeBundleSize,
  generateOptimizationReport,
  displayResults,
  applyOptimizations,
  runBundleAnalysis
};
