import React, { useState } from "react";
import "./main.css";

const SIDE = 100;
const COLORS = ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"];

function PolyPlace() {
  const [grid, setGrid] = useState(Array(SIDE * SIDE).fill("white"));
  const [selectedColor, setSelectedColor] = useState("black");
  const [coordinates, setCoordinates] = useState("(0,0)");

  const handleClick = (index) => {
    const newGrid = [...grid];
    newGrid[index] = selectedColor;
    setGrid(newGrid);
  };

  const handleMouse = (index) => {
    const x = index % SIDE;
    const y = Math.floor(index / SIDE);
    setCoordinates(`(${x},${y})`);
  };

  return (
    <div className="polyplace-container">
      {/* Navigation Bar */}
      <nav className="navbar">
        <h1>PolyPlace</h1>
      </nav>

      <div className="main-content">
        {/* Canvas Container */}
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

        {/* Sidebar */}
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
