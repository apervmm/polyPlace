import React, {
  useState, 
  useEffect, 
  useRef, 
  useCallback
} from "react";


const BOARD_W  = 960;
const BOARD_H  = 540;
const MIN_ZOOM = 1;    
const MAX_ZOOM = 6; 
const PAN_SPEED = 80;

const COLORS = ["#ff0000","#0000ff","#008000","#ffff00","#000000","#ffffff","#800080","#ffa500"];

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [
    (n >> 16) & 255,
    (n >> 8) & 255,
    n & 255
  ];
} 


const ADDR = "wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net";
// const ADDR = "ws://localhost:8765";


function clamp(val, min, max) { 
  return Math.max(min, Math.min(max, val)); 
}



function helper(xPx, yPx, view, zoom, viewPxW, viewPxH) {
  const vx = xPx / viewPxW;          
  const vy = yPx / viewPxH;
  return {
    bx : Math.floor(view.x + vx * BOARD_W / zoom),
    by : Math.floor(view.y + vy * BOARD_H / zoom)
  };
}





export default function PolyPlace({ token, logout, openAuth })
{
  const viewCanvas = useRef(null);       
  const boardCanvas = useRef(null);       
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

    vCtx.imageSmoothingEnabled = false;

    const vw = BOARD_W / camera.zoom;
    const vh = BOARD_H / camera.zoom;
    vCtx.clearRect(0,0, vCtx.canvas.width, vCtx.canvas.height);
    vCtx.drawImage(boardCanvas.current,
      camera.x, camera.y, vw, vh,
      0, 0, vCtx.canvas.width, vCtx.canvas.height
    );
  }, [camera]);




  /* fitting canvas */
  useEffect(() => {

    function fit() {
      const node = viewCanvas.current;
      const w = window.innerWidth;
      const h = window.innerHeight;
      const size = Math.floor(Math.min(w, h*16/9));
      node.width  = size;
      node.height = Math.floor(size * 9/16);
      // redraw();
    }

    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [redraw]);



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

    const vx = (e.clientX - rect.left) / rect.width;
    const vy = (e.clientY - rect.top) / rect.height;
    

    const bx = camera.x + vx * BOARD_W / camera.zoom;
    const by = camera.y + vy * BOARD_H / camera.zoom;

    const newZoom = clamp(
      camera.zoom * (e.deltaY > 0 ? 0.9 : 1.1),
      MIN_ZOOM, MAX_ZOOM
    );


    const vw = BOARD_W / newZoom;
    const vh = BOARD_H / newZoom;

    const newCam = {
      zoom : newZoom,
      // x : clamp(bx - vw * 0.5, 0, BOARD_W - vw),
      // y : clamp(by - vh * 0.5, 0, BOARD_H - vh)
      x : clamp(bx - vw * vx, 0, BOARD_W - vw),  
      y : clamp(by - vh * vy, 0, BOARD_H - vh)
    };
    setCamera(newCam);
  };

  /* drag */
  const dragRef = useRef(null);  

  const startDrag =(e) => { 
    dragRef.current = {
      x: e.clientX, 
      y: e.clientY
    };
  };

  const endDrag = () => { 
    dragRef.current = null; 
  };

  const moveDrag = (e) => {
    if (!dragRef.current) return;

    const dx = e.clientX - dragRef.current.x;
    const dy = e.clientY - dragRef.current.y;


    dragRef.current = {
      x: e.clientX, 
      y: e.clientY
    };

    const rect = viewCanvas.current;
    const vwPx = rect.width, vhPx = rect.height;

    const speed = (MAX_ZOOM / camera.zoom) * PAN_SPEED; 

    const nx = camera.x - dx * BOARD_W / (camera.zoom*vwPx) * speed/100;
    const ny = camera.y - dy * BOARD_H / (camera.zoom*vhPx) * speed/100;

    const newCam = {
      ...camera,
      x : clamp(nx, 0, BOARD_W - BOARD_W/camera.zoom),
      y : clamp(ny, 0, BOARD_H - BOARD_H/camera.zoom)
    };
    setCamera(newCam);
  };

  // place a pixel 
  const place = (e) => {
    if (!token) {
      openAuth();
      return;
    }

    const rect = viewCanvas.current.getBoundingClientRect();

    const { bx, by } = helper(e.clientX - rect.left, e.clientY - rect.top, camera, camera.zoom, rect.width, rect.height);


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
      camera, camera.zoom, rect.width, rect.height
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

        <div className="sidebar">
          <div className="coordinates">Coords: {coords}</div>
          <div className="palette">
            {COLORS.map(c=>(
              <button key={c}
                  className="color-button"
                  style={{backgroundColor:c,
                          border:c===colour?"2px solid #000":"1px solid #ccc"}}
                  onClick={()=>setColour(c)}/>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
