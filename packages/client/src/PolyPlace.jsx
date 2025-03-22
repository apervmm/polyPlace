import React, { useState, useEffect, useRef } from "react";
// import "dotenv/config";
// import "./main.css";


const WIDTH = 160;
const HEIGHT = 100;
const COLORS = ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"];

const Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI4NWQxY2UxOS1lYzg0LTQ2YmUtOGQ1Zi04YzY4ODU5ZjgzZmYiLCJpYXQiOjE3NDI2Mjk1NDAsImV4cCI6MTc0MjcxNTk0MH0.LQejAdRQbyhD98JBJ9W3bNn_1FXIiLFt4ISIg-XWYYw";


function PolyPlace() {
  const [grid, setGrid] = useState(Array(WIDTH * HEIGHT).fill("white"));
  const [selectedColor, setSelectedColor] = useState("black");
  const [coordinates, setCoordinates] = useState("(0,0)");
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8765?token=${Token}`);
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

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

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

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
