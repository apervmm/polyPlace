import React, {
  useState, 
  useEffect, 
  useRef, 
  useCallback
} from "react";


const BOARD_W  = 540;
const BOARD_H  = 540;
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 40;

const COLORS = ["#ff0000","#0000ff","#008000","#ffff00","#000000","#ffffff","#800080","#ffa500"];

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [
    (n >> 16) & 255,
    (n >> 8) & 255,
    n & 255
  ];
} 


// const ADDR = "wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net";
const ADDR = "ws://localhost:8765";


function clamp(val, min, max) { 
  return Math.max(min, Math.min(max, val)); 
}



// New zoom model: zoom=N means each board pixel = N canvas pixels.
// At zoom=1, canvas pixels map 1:1 to board pixels (no BOARD_W dependency).
function helper(xPx, yPx, view, zoom) {
  return {
    bx : Math.floor(view.x + xPx / zoom),
    by : Math.floor(view.y + yPx / zoom)
  };
}





export default function PolyPlace({ token, logout, openAuth })
{
  const viewCanvas = useRef(null);
  const boardCanvas = useRef(null);
  const canvasPanelRef = useRef(null);
  const wsRef = useRef(null);

  const [camera, setCamera] = useState({ x:0, y:0, zoom:1 });  
  const [coords, setCoords] = useState("(0,0)");
  const [colour, setColour] = useState("black");



  useEffect(() => {
    const off = document.createElement("canvas");
    off.width  = BOARD_W;
    off.height = BOARD_H;
    const oCtx = off.getContext("2d");
    const img  = oCtx.createImageData(BOARD_W, BOARD_H);    

    for (let i = 0; i < img.data.length; i += 4) img.data[i] = 0;

    oCtx.putImageData(img, 0, 0);
    boardCanvas.current = off;

    const ws = new WebSocket(token ? `${ADDR}/?token=${token}` : ADDR);

    wsRef.current = ws;

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.error) { 
        if (token) {
          ws.close(); 
          logout(); 
        }
        return; 
      }



      const paint = (idx, col) => {
        const [r,g,b] = hexToRgb(col);
        img.data[idx+0]=r; 
        img.data[idx+1]=g; 
        img.data[idx+2]=b; 
        img.data[idx+3]=255;
      };

      if (msg.type === "init") {
        msg.pixels.forEach(({x, y, color}) => paint((y * BOARD_W + x) * 4, color));
        oCtx.putImageData(img, 0, 0);
      }


      if (msg.type === "update") {
        paint((msg.y*BOARD_W + msg.x)*4, msg.color);
        oCtx.putImageData(img, 0, 0);
      }
    };

    ws.onerror = () => {
      ws.close(); 
      logout(); 
    };
    return () => ws.close();
  }, [token, logout]);





  const redraw = useCallback(() =>
  {
    const vCtx = viewCanvas.current.getContext("2d");
    const cw = vCtx.canvas.width;
    const ch = vCtx.canvas.height;
    const z = camera.zoom;

    vCtx.imageSmoothingEnabled = false;

    // Infinite canvas background
    vCtx.fillStyle = '#666';
    vCtx.fillRect(0, 0, cw, ch);

    // Apply camera transform:
    //   board (bx, by) → canvas ((bx - camera.x)*z, (by - camera.y)*z)
    vCtx.save();
    vCtx.translate(-camera.x * z, -camera.y * z);
    vCtx.scale(z, z);

    // White board background (unset pixels appear white, not gray)
    vCtx.fillStyle = '#fff';
    vCtx.fillRect(0, 0, BOARD_W, BOARD_H);

    // Draw board pixels
    vCtx.drawImage(boardCanvas.current, 0, 0);

    // Board border — 1 canvas pixel wide at any zoom
    vCtx.strokeStyle = '#000';
    vCtx.lineWidth = 1 / z;
    vCtx.strokeRect(0, 0, BOARD_W, BOARD_H);

    vCtx.restore();
  }, [camera]);



  useEffect(() => {
    const node = viewCanvas.current;
    const panel = canvasPanelRef.current;

    function fitDisplay() {
      const w = panel.clientWidth;
      const h = panel.clientHeight;
      // intrinsic resolution = display size: 1 canvas pixel = 1 screen pixel, no CSS scaling
      node.width        = w;
      node.height       = h;
      node.style.width  = `${w}px`;
      node.style.height = `${h}px`;
    }
    fitDisplay();
    const ro = new ResizeObserver(fitDisplay);
    ro.observe(panel);
    return () => ro.disconnect();
  }, []);



  /* animation */
  useEffect(() => {
    let animId;
    function loop()
    { 
      redraw(); 
      animId = requestAnimationFrame(loop); 
    }
    
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);

  }, [redraw]);





  const handleWheel = (e) => {
    // e.preventDefault();

    const rect = viewCanvas.current.getBoundingClientRect();
    // console.log(rect);


    // const { bx, by } = helper(
    //   e.clientX - rect.left, e.clientY - rect.top,
    //   camera, camera.zoom, rect.width, rect.height
    // );

    const cw = rect.width;
    const ch = rect.height;
    const vx = (e.clientX - rect.left) / cw;
    const vy = (e.clientY - rect.top)  / ch;

    // board position under cursor
    const bx = camera.x + vx * cw / camera.zoom;
    const by = camera.y + vy * ch / camera.zoom;

    const newZoom = clamp(
      camera.zoom * (e.deltaY > 0 ? 0.9 : 1.1),
      MIN_ZOOM, MAX_ZOOM
    );

    const vw = cw / newZoom;
    const vh = ch / newZoom;

    const newCam = {
      zoom : newZoom,
      x : clamp(bx - vw * vx, -vw / 2, BOARD_W - vw / 2),
      y : clamp(by - vh * vy, -vh / 2, BOARD_H - vh / 2)
    };
    setCamera(newCam);
  };

  /* drag */
  const dragRef = useRef(null);  
  const draggedRef = useRef(false);

  const startDrag =(e) => { 
    dragRef.current = {
      x: e.clientX, 
      y: e.clientY
    };
    draggedRef.current = false;
  };

  const endDrag = () => { 
    dragRef.current = null; 
  };

  const moveDrag = (e) => {
    if (!dragRef.current) return;

    const dx = e.clientX - dragRef.current.x;
    const dy = e.clientY - dragRef.current.y;


    if (Math.abs(dx) > 2 || Math.abs(dy) > 2)           
      draggedRef.current = true;


    dragRef.current = {
      x: e.clientX, 
      y: e.clientY
    };

    const cw = viewCanvas.current.width;
    const ch = viewCanvas.current.height;
    const vw = cw / camera.zoom;
    const vh = ch / camera.zoom;

    // 1 canvas pixel dragged = 1/zoom board pixels panned
    const nx = camera.x - dx / camera.zoom;
    const ny = camera.y - dy / camera.zoom;

    const newCam = {
      ...camera,
      x : clamp(nx, -vw / 2, BOARD_W - vw / 2),
      y : clamp(ny, -vh / 2, BOARD_H - vh / 2)
    };
    setCamera(newCam);
  };

  // place a pixel 
  const place = (e) => {
    if (draggedRef.current) {
      draggedRef.current = false;
      return;
    }

    if (!token) {
      openAuth();
      return;
    }

    const rect = viewCanvas.current.getBoundingClientRect();

    const { bx, by } = helper(e.clientX - rect.left, e.clientY - rect.top, camera, camera.zoom);


    if (bx < 0 || bx >= BOARD_W || by < 0 || by >= BOARD_H) return;

    wsRef.current.send(JSON.stringify({
      type:"place", 
      x: bx,
      y: by,
      // coordinate: by*BOARD_W + bx, 
      color: colour
    }));
  };

  const hover = e => {
    const rect = viewCanvas.current.getBoundingClientRect();
    const { bx, by } = helper(
      e.clientX - rect.left, e.clientY - rect.top,
      camera, camera.zoom
    );
    setCoords(`(${bx},${by})`);
  };

  return (
    <div className="polyplace-container">
      <nav className="navbar">

        <h1>p/Place</h1>

        <button
          className="nav-btn"
          onClick={() => (token ? logout() : openAuth())}
          >
          {token ? "Logout" : "Login"}
        </button>
        
      </nav>

      <div className="main-content">

        <div className="canvas-panel" ref={canvasPanelRef}>
          <canvas
            ref={viewCanvas}
            className="canvas"
            onWheel={handleWheel}
            onMouseDown={startDrag}
            onMouseMove={e=>{moveDrag(e); hover(e);}}
            onMouseUp={endDrag}
            onMouseLeave={endDrag}
            onClick={place}
          />

          <div className="coords-overlay">{coords}</div>

          <div className="color-overlay">
            {COLORS.map(c=>(
              <button key={c}
                className="color-button"
                style={{backgroundColor:c,
                        outline:c===colour?"3px solid #000":"none"}}
                onClick={()=>setColour(c)}/>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
