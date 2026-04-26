const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let pythonProcess = null;

const isDev = process.env.NODE_ENV !== 'production';

// Paths — main.js lives in frontend/electron/
const PROJECT_ROOT = path.join(__dirname, '..', '..');

const RESOURCES_DIR = isDev
  ? path.join(__dirname, '..')
  : path.join(process.resourcesPath, 'app');

const PYTHON_BACKEND = isDev
  ? path.join(PROJECT_ROOT, '.venv', 'bin', 'python3')
  : path.join(process.resourcesPath, 'backend', 'backend');

const BACKEND_DIR = isDev
  ? path.join(PROJECT_ROOT, 'backend')
  : path.join(process.resourcesPath, 'backend');

function startPythonBackend() {
  return new Promise((resolve, reject) => {
    if (isDev) {
      pythonProcess = spawn(PYTHON_BACKEND, [
        '-m', 'uvicorn', 'main:app',
        '--host', '127.0.0.1', '--port', '8100',
      ], {
        cwd: BACKEND_DIR,
        env: { ...process.env, PYTHONPATH: BACKEND_DIR },
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    } else {
      // Production: use PyInstaller-bundled executable
      pythonProcess = spawn(PYTHON_BACKEND, [], {
        cwd: BACKEND_DIR,
        env: {
          ...process.env,
          DATA_DIR: path.join(app.getPath('userData'), 'data'),
        },
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    }

    pythonProcess.stdout.on('data', (data) => {
      console.log(`[backend] ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`[backend] ${data}`);
    });

    pythonProcess.on('error', reject);
    pythonProcess.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        reject(new Error(`Backend exited with code ${code}`));
      }
    });

    // Poll until ready
    const maxRetries = 30;
    let retries = 0;
    const checkReady = () => {
      http.get('http://127.0.0.1:8100/api/health', (res) => {
        if (res.statusCode === 200) {
          console.log('[electron] Backend ready');
          resolve();
        } else if (retries < maxRetries) {
          retries++;
          setTimeout(checkReady, 500);
        } else {
          reject(new Error('Backend health check failed'));
        }
      }).on('error', () => {
        if (retries < maxRetries) {
          retries++;
          setTimeout(checkReady, 500);
        } else {
          reject(new Error('Backend did not start'));
        }
      });
    };
    setTimeout(checkReady, 1500);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: '高企&小巨人智能申报系统',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5178');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(RESOURCES_DIR, 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => { mainWindow = null; });
}

ipcMain.handle('get-app-version', () => app.getVersion());

app.whenReady().then(async () => {
  try {
    await startPythonBackend();
    createWindow();
  } catch (err) {
    console.error('[electron] Failed to start:', err);
    createWindow(); // Still open UI, backend will show errors
  }
});

app.on('window-all-closed', () => {
  if (pythonProcess) { pythonProcess.kill(); pythonProcess = null; }
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) createWindow();
});

app.on('before-quit', () => {
  if (pythonProcess) { pythonProcess.kill(); pythonProcess = null; }
});
