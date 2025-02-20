import React, { useState, useEffect } from "react";

const SIDE = 100;
const COLORS = ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"];
const ws = new WebSocket("ws://localhost:8765");

function PolyPlace() {
  const [grid, setGrid] = useState(Array(SIDE * SIDE).fill("white"));
  const [selectedColor, setSelectedColor] = useState("black");
  const [coordinates, setCoordinates] = useState("(0,0)");

  useEffect(() => {
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "grid") {
        setGrid(message.data);
      } else if (message.type === "update") {
        setGrid((prevGrid) => {
          const newGrid = [...prevGrid];
          newGrid[message.index] = message.color;
          return newGrid;
        });
      }
    };

    return () => ws.close();
  }, []);

  const handleClick = (index) => {
    ws.send(JSON.stringify({ type: "place", index, color: selectedColor }));
  };

  const handleMouse = (index) => {
    const x = index % SIDE;
    const y = Math.floor(index / SIDE);
    setCoordinates(`(${x},${y})`);
  };

  return (
    <div className="polyplace-container">
      <nav className="navbar">
        <h1>PolyPlace</h1>
      </nav>

      <div className="main-content">
        <div className="canvas-container">
          <div className="canvas">
            {grid.map((color, index) => (
              <div
                key={index}
                className="pixel"
                style={{ backgroundColor: color }}
                onClick={() => handleClick(index)}
                onMouseMove={() => handleMouse(index)}
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
