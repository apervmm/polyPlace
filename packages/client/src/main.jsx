import React from "react";
import ReactDOMClient from "react-dom/client";
import PolyPlace from "./PolyPlace";
import App from "./App";
import "./main.css";

const container = document.getElementById("root");
const root = ReactDOMClient.createRoot(container);
root.render(<PolyPlace />);