import React, { useState, useEffect, useRef } from "react";
// import "dotenv/config";
// import "./main.css";


const WIDTH = 160;
const HEIGHT = 100;
const COLORS = ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"];

function PolyPlace({ token }) {
  const [grid, setGrid] = useState(Array(WIDTH * HEIGHT).fill("white"));
  const [selectedColor, setSelectedColor] = useState("black");
  const [coordinates, setCoordinates] = useState("(0,0)");
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net/?token=${token}`);
    // const ws = new WebSocket(`wss://wwserver-hye8emhqc7cfcgef.westus3-01.azurewebsites.net/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjOGRlZTU1Ny0yMzg4LTQ3YjctOTk5ZC1iODY3ODdiYzMzNGIiLCJpYXQiOjE3NDUzNDUzMzksImV4cCI6MTc0NTQzMTczOX0.Ir99--W-ZlD1koA4O93dEGf1bwiV1hnOqo88ENf-kP4`);
    
    
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);


      if (msg.error) {
        console.error("WS error:", msg.error);
        ws.close();
        logout();
        return;
      }

      if (message.type === "init") {
        const newGrid = Array(WIDTH * HEIGHT).fill("white");

        message.pixels.forEach((pix) => {
          newGrid[pix.coordinate] = pix.color;
        });
        setGrid(newGrid);
      } else if (message.type === "update") {
        setGrid((prevGrid) => {
          const newGrid = [...prevGrid];
          newGrid[message.coordinate] = message.color;
          return newGrid;
        });
      }
    };


    ws.onclose = () => {
      if (!initReceived) {
        logout();
      }
    };


    
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [token]);

  const handleClick = (coordinate) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "place",
        coordinate,
        color: selectedColor
      }));
    }
  };

  const handleMouse = (coordinate) => {
    const x = coordinate % WIDTH;
    const y = Math.floor(coordinate / WIDTH);
    setCoordinates(`(${x},${y})`);
  };

  return (
    <div className="polyplace-container">
      <nav className="navbar">
        <h1>PolyPlace</h1>
      </nav>

      <div className="main-content">
        <div className="canvas-container">
          <div
            className="canvas"
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${WIDTH}, 1fr)`,
              gridTemplateRows: `repeat(${HEIGHT}, 1fr)`
            }}>
            {grid.map((color, coordinate) => (
              <div
                key={coordinate}
                className="pixel"
                style={{ backgroundColor: color }}
                onClick={() => handleClick(coordinate)}
                onMouseMove={() => handleMouse(coordinate)}
              />
            ))}
          </div>
        </div>

        <div className="sidebar">
          <div className="coordinates">Coordinates: {coordinates}</div>
          <div className="palette">
            {COLORS.map((color) => (
              <button
                key={color}
                className="color-button"
                style={{ backgroundColor: color }}
                onClick={() => setSelectedColor(color)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PolyPlace;