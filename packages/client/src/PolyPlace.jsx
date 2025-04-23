import React, {
  useState,
  useEffect,
  useRef,
  useCallback
} from "react";

const WIDTH = 1000;
const HEIGHT = 1000;
const COLORS = [
  "red", "blue", "green", "yellow",
  "black","white","purple","orange"
];

// map your eight CSS names → [r, g, b]
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
  // we no longer store an array of 16 000 colors in React—
  // the pixel buffer lives in the canvas’s ImageData.
  const [coords, setCoords]     = useState("(0,0)");
  const [selected, setSelected] = useState("black");
  const imageDataRef            = useRef(null);
  
  // helper to draw the entire buffer (or a dirty rect)
  const draw = useCallback((dirty) => {
    const ctx = canvasRef.current.getContext("2d");
    if (!dirty) {
      // full-canvas draw:
      ctx.putImageData(imageDataRef.current, 0, 0);
    } else {
      // only redraw a single pixel region:
      const { x, y } = dirty;
      ctx.putImageData(
        imageDataRef.current,
        0, 0,
        x, y, 1, 1
      );
    }
  }, []);
  
  // initialize canvas + WS
  useEffect(() => {
    const canvas = canvasRef.current;
    canvas.width  = WIDTH;
    canvas.height = HEIGHT;
    const ctx = canvas.getContext("2d");
    
    // make a blank white buffer
    const img = ctx.createImageData(WIDTH, HEIGHT);
    for (let i = 0; i < img.data.length; i += 4) {
      img.data[i + 0] = 255; // R
      img.data[i + 1] = 255; // G
      img.data[i + 2] = 255; // B
      img.data[i + 3] = 255; // A
    }
    ctx.putImageData(img, 0, 0);
    imageDataRef.current = img;
    
    // open websocket
    const ws = new WebSocket(
      `wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net/?token=${token}`
    );
    wsRef.current = ws;
    
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      
      // on auth error, bail back to login
      if (msg.error) {
        ws.close();
        logout();
        return;
      }
      
      // initial full state
      if (msg.type === "init") {
        msg.pixels.forEach(({ coordinate, color }) => {
          const [r, g, b] = COLOR_MAP[color];
          const idx = coordinate * 4;
          img.data[idx + 0] = r;
          img.data[idx + 1] = g;
          img.data[idx + 2] = b;
          img.data[idx + 3] = 255;
        });
        draw();  // repaint everything
      }
      
      // single-pixel update
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
  
  // update the hover coords display
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
            border: "2px solid black"
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




// import React, { useState, useEffect, useRef, useCallback } from "react";
// // import "dotenv/config";
// // import "./main.css";


// const WIDTH = 100;
// const HEIGHT = 100;
// const COLORS = ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"];

// function PolyPlace({ token, logout }) {
//   const [grid, setGrid] = useState(Array(WIDTH * HEIGHT).fill("white"));
//   const [selectedColor, setSelectedColor] = useState("black");
//   const [coordinates, setCoordinates] = useState("(0,0)");
//   const wsRef = useRef(null);

//   useEffect(() => {
//     const ws = new WebSocket(`wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net/?token=${token}`);
    
    
    
//     ws.onmessage = (event) => {
//       const message = JSON.parse(event.data);


//       if (message.error) {
//         console.error("WS error:", message.error);
//         ws.close();
//         logout();
//         return;
//       }

//       if (message.type === "init") {
//         const newGrid = Array(WIDTH * HEIGHT).fill("white");

//         message.pixels.forEach((pix) => {
//           newGrid[pix.coordinate] = pix.color;
//         });
//         setGrid(newGrid);
//       } else if (message.type === "update") {
//         setGrid((prevGrid) => {
//           const newGrid = [...prevGrid];
//           newGrid[message.coordinate] = message.color;
//           return newGrid;
//         });
//       }
//     };


    
//     wsRef.current = ws;

//     return () => {
//       ws.close();
//     };
//   }, [token, logout]);

//   const handleClick = (coordinate) => {
//     if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
//       wsRef.current.send(JSON.stringify({
//         type: "place",
//         coordinate,
//         color: selectedColor
//       }));
//     }
//   };

//   const handleMouse = (coordinate) => {
//     const x = coordinate % WIDTH;
//     const y = Math.floor(coordinate / WIDTH);
//     setCoordinates(`(${x},${y})`);
//   };

//   return (
//     <div className="polyplace-container">
//       <nav className="navbar">
//         <h1>PolyPlace</h1>
//       </nav>

//       <div className="main-content">
//         <div className="canvas-container">
//           <div
//             className="canvas"
//             style={{
//               display: "grid",
//               gridTemplateColumns: `repeat(${WIDTH}, 1fr)`,
//               gridTemplateRows: `repeat(${HEIGHT}, 1fr)`
//             }}>
//             {grid.map((color, coordinate) => (
//               <div
//                 key={coordinate}
//                 className="pixel"
//                 style={{ backgroundColor: color }}
//                 onClick={() => handleClick(coordinate)}
//                 onMouseMove={() => handleMouse(coordinate)}
//               />
//             ))}
//           </div>
//         </div>

//         <div className="sidebar">
//           <div className="coordinates">Coordinates: {coordinates}</div>
//           <div className="palette">
//             {COLORS.map((color) => (
//               <button
//                 key={color}
//                 className="color-button"
//                 style={{ backgroundColor: color }}
//                 onClick={() => setSelectedColor(color)}
//               />
//             ))}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default PolyPlace;