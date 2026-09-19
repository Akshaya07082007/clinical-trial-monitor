import express from "express";
import path from "path";
import http from "http";
import { spawn, ChildProcess } from "child_process";
import { createServer as createViteServer } from "vite";

const PORT = 3000;
const PYTHON_PORT = 8085;

let pythonProcess: ChildProcess | null = null;

function startPythonBackend() {
  console.log(`[Server] Starting Python API on port ${PYTHON_PORT}...`);
  pythonProcess = spawn("python3", ["server.py", "--port", String(PYTHON_PORT)], {
    stdio: "inherit",
    detached: false
  });

  pythonProcess.on("exit", (code, signal) => {
    console.log(`[Server] Python process exited with code ${code} and signal ${signal}`);
  });
}

function proxyToPython(req: express.Request, res: express.Response) {
  const options: http.RequestOptions = {
    hostname: "127.0.0.1",
    port: PYTHON_PORT,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: `127.0.0.1:${PYTHON_PORT}`
    }
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on("error", (err) => {
    console.error(`[Proxy Error] Unable to connect to Python backend on ${PYTHON_PORT}:`, err.message);
    res.status(502).json({
      error: "Python monitoring backend is starting or unavailable",
      details: err.message
    });
  });

  req.pipe(proxyReq, { end: true });
}

async function startServer() {
  startPythonBackend();

  // Wait 1.5s for Python server socket to bind
  await new Promise((r) => setTimeout(r, 1500));

  const app = express();
  app.use(express.json());

  // Direct Express API routes & Proxy routes to Python backend
  const proxyPaths = [
    "/api",
    "/health",
    "/cycles",
    "/escalations",
    "/queries",
    "/trace",
    "/knowledge-graph",
    "/risk-radar",
    "/protocol",
    "/deviations",
    "/findings"
  ];

  proxyPaths.forEach((routePrefix) => {
    app.use(routePrefix, (req, res) => {
      proxyToPython(req, res);
    });
  });

  // Vite development middleware vs Static Production
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`[Express] Clinical Trial Review System running on http://0.0.0.0:${PORT}`);
  });

  const cleanup = () => {
    if (pythonProcess) {
      pythonProcess.kill();
    }
    server.close();
    process.exit(0);
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);
}

startServer();
