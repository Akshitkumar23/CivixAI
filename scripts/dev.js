/**
 * CivixAI Full-Stack Development Launcher
 * Runs Python FastAPI Backend (Port 8000) and Next.js Frontend (Port 3000) concurrently.
 */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.resolve(__dirname, '..');

// 1. Resolve Python Binary (prioritize local .venv)
let pythonBin = 'python';
const venvWin = path.join(rootDir, '.venv', 'Scripts', 'python.exe');
const venvUnix = path.join(rootDir, '.venv', 'bin', 'python');

if (fs.existsSync(venvWin)) {
  pythonBin = venvWin;
} else if (fs.existsSync(venvUnix)) {
  pythonBin = venvUnix;
}

console.log('\n======================================================');
console.log('  🚀 CivixAI Full-Stack Development Environment');
console.log('======================================================');
console.log(`  🐍 Backend API : http://127.0.0.1:8000 (Python: ${path.relative(rootDir, pythonBin)})`);
console.log('  🌐 Frontend UI : http://127.0.0.1:3000');
console.log('======================================================\n');

// 2. Spawn FastAPI Backend (Port 8000)
const backend = spawn(pythonBin, [
  '-m', 'uvicorn',
  'services.ml_api.main:app',
  '--host', '127.0.0.1',
  '--port', '8000',
  '--reload'
], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true,
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
});

// 3. Spawn Next.js Frontend (Port 3000)
const nextBin = path.join(rootDir, 'node_modules', '.bin', process.platform === 'win32' ? 'next.cmd' : 'next');
const frontendCmd = fs.existsSync(nextBin) ? nextBin : (process.platform === 'win32' ? 'npx.cmd' : 'npx');
const frontendArgs = fs.existsSync(nextBin) ? ['dev', '-H', '127.0.0.1'] : ['next', 'dev', '-H', '127.0.0.1'];

const frontend = spawn(frontendCmd, frontendArgs, {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true,
  env: process.env
});

// 4. Graceful Cleanup Handler
function cleanup() {
  console.log('\n🛑 [CivixAI] Stopping all development servers...');
  
  if (backend && !backend.killed) {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', backend.pid, '/f', '/t'], { stdio: 'ignore' });
    } else {
      backend.kill('SIGTERM');
    }
  }

  if (frontend && !frontend.killed) {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', frontend.pid, '/f', '/t'], { stdio: 'ignore' });
    } else {
      frontend.kill('SIGTERM');
    }
  }
}

process.on('SIGINT', () => { cleanup(); process.exit(0); });
process.on('SIGTERM', () => { cleanup(); process.exit(0); });
process.on('exit', () => { cleanup(); });

backend.on('error', (err) => {
  console.error('❌ Failed to start Backend server:', err);
});

frontend.on('error', (err) => {
  console.error('❌ Failed to start Frontend server:', err);
});
