import React, { useState, useEffect } from "react";
import Auth from "./Auth";
import PolyPlace from "./PolyPlace";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token") || null);



  return (
    <div>
      {!token ? (
        <Auth setToken={setToken} />
      ) : (
        <PolyPlace token={token} />
      )}
    </div>
  );
}

export default App;
