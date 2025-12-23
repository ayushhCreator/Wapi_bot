#!/usr/bin/env node

/**
 * Cleanup script - Frees ports 3000-3009 on startup and handles graceful shutdown
 */

const { execSync } = require('child_process');
const path = require('path');

// Function to kill processes on specific ports
function killPortsOnStartup() {
  console.log('🧹 Cleaning up ports 3000-3009...');
  for (let port = 3000; port <= 3009; port++) {
    try {
      execSync(`fuser -k ${port}/tcp 2>/dev/null`, { stdio: 'ignore' });
    } catch (e) {
      // Port already free, ignore
    }
  }
  console.log('✓ Ports cleaned\n');
}

// Function to cleanup on exit
function setupGracefulShutdown() {
  const signals = ['SIGINT', 'SIGTERM', 'SIGHUP', 'SIGQUIT'];

  signals.forEach(signal => {
    process.on(signal, () => {
      console.log(`\n🛑 Received ${signal}, cleaning up ports...`);
      for (let port = 3000; port <= 3009; port++) {
        try {
          execSync(`fuser -k ${port}/tcp 2>/dev/null`, { stdio: 'ignore' });
        } catch (e) {
          // Ignore
        }
      }
      console.log('✓ Ports freed, exiting...\n');
      process.exit(0);
    });
  });
}

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  console.error('\n❌ Uncaught Exception:', err.message);
  console.log('🧹 Cleaning up ports on crash...');
  for (let port = 3000; port <= 3009; port++) {
    try {
      execSync(`fuser -k ${port}/tcp 2>/dev/null`, { stdio: 'ignore' });
    } catch (e) {
      // Ignore
    }
  }
  console.log('✓ Ports freed\n');
  process.exit(1);
});

// Run cleanup on startup
killPortsOnStartup();
setupGracefulShutdown();

// Run the actual Next.js dev server
const { spawn } = require('child_process');
const nextDev = spawn('next', ['dev', '-p', '3000'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true,
});

nextDev.on('error', (err) => {
  console.error('Failed to start dev server:', err);
  process.exit(1);
});
