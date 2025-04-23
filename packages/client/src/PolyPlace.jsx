import React, {
  useState,
  useEffect,
  useRef,
  useCallback
} from "react";

const WIDTH =200;
const HEIGHT = 200;

const COLORS = [
  "red", "blue", "green", "yellow",
  "black","white","purple","orange"
];

const COLOR_MAP = {
  red:    [255,   0,   0],
  blue:   [  0,   0, 255],
  green:  [  0, 128,   0],
  yellow: [255, 255,   0],
  black:  [  0,   0,   0],
  white:  [255, 255, 255],
  purple: [128,   0, 128],
  orange: [255, 165,   0],
};

export default function PolyPlace({ token, logout }) {
  const canvasRef = useRef(null);
  const wsRef     = useRef(null);
  const [coords, setCoords]     = useState("(0,0)");
  const [selected, setSelected] = useState("black");
  const imageDataRef = useRef(null);
  


  // helper for buffer
  const draw = useCallback((dirty) => {
    const ctx = canvasRef.current.getContext("2d");
    if (!dirty) {
      ctx.putImageData(imageDataRef.current, 0, 0);
    } else {
      const { x, y } = dirty;
      ctx.putImageData(
        imageDataRef.current,
        0, 0,
        x, y, 1, 1
      );
    }
  }, []);
  



  useEffect(() => {
    const canvas = canvasRef.current;
    canvas.width  = WIDTH;
    canvas.height = HEIGHT;
    const ctx = canvas.getContext("2d");
    
    // create black white map
    const img = ctx.createImageData(WIDTH, HEIGHT);
    for (let i = 0; i < img.data.length; i += 4) {
      img.data[i + 0] = 255; // R
      img.data[i + 1] = 255; // G
      img.data[i + 2] = 255; // B
      img.data[i + 3] = 0; // A
    }



    ctx.putImageData(img, 0, 0);
    imageDataRef.current = img;
    
    const ws = new WebSocket(`wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net/?token=${token}`);
    wsRef.current = ws;
    
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.error) {
        ws.close();
        logout();
        return;
      }
      


      // init
      if (msg.type === "init") {
        msg.pixels.forEach(({ coordinate, color }) => {
          const [r, g, b] = COLOR_MAP[color];
          const idx = coordinate * 4;
          img.data[idx + 0] = r;
          img.data[idx + 1] = g;
          img.data[idx + 2] = b;
          img.data[idx + 3] = 255;
        });
        draw(); 
      }
      

      // update
      else if (msg.type === "update") {
        const { coordinate, color } = msg;
        const [r, g, b] = COLOR_MAP[color];
        const idx = coordinate * 4;
        img.data[idx + 0] = r;
        img.data[idx + 1] = g;
        img.data[idx + 2] = b;
        img.data[idx + 3] = 255;
        
        const x = coordinate % WIDTH;
        const y = Math.floor(coordinate / WIDTH);
        draw({ x, y });
      }
    };
    
    ws.onerror = () => { ws.close(); logout(); };
    return () => { ws.close(); };
  }, [token, logout, draw]);
  
  // send a place command
  const place = useCallback((evt) => {
    const rect = canvasRef.current.getBoundingClientRect();
    // translate click pixel → grid coordinate
    const x = Math.floor((evt.clientX - rect.left) * WIDTH / rect.width);
    const y = Math.floor((evt.clientY - rect.top)  * HEIGHT/ rect.height);
    const coord = y * WIDTH + x;
    
    wsRef.current.send(JSON.stringify({
      type: "place",
      coordinate: coord,
      color: selected
    }));
  }, [selected]);
  
  const hover = useCallback((evt) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.floor((evt.clientX - rect.left) * WIDTH / rect.width);
    const y = Math.floor((evt.clientY - rect.top)  * HEIGHT/ rect.height);
    setCoords(`(${x},${y})`);
  }, []);
  
  return (
    <div className="polyplace-container">
      <nav className="navbar"><h1>PolyPlace</h1></nav>
      <div className="main-content">
        <canvas
          ref={canvasRef}
          className="canvas"
          onClick={place}
          onMouseMove={hover}
          style={{
            width:  "90vw",
            height: "90vh",
            // border: "2px solid black"
          }}
        />
        <div className="sidebar">
          <div className="coordinates">Coordinates: {coords}</div>
          <div className="palette">
            {COLORS.map(c => (
              <button
                key={c}
                className="color-button"
                style={{ backgroundColor: c }}
                onClick={() => setSelected(c)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

