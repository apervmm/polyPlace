import React, { useState, useEffect } from "react";
import Auth from "./Auth";
import PolyPlace from "./PolyPlace";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [showAuth, setShowAuth] = useState(false);

  const openAuth   = () => setShowAuth(true);
  const closeAuth  = () => setShowAuth(false);


  function handleLogout() {
    localStorage.removeItem("token");
    setToken(null);
  }

  
  return (
    <>
      <PolyPlace
        token={token}
        logout={handleLogout}
        openAuth={openAuth} 
      />

      {showAuth && (
        <div className="modal-overlay" onClick={closeAuth}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <Auth
              setToken={t => { setToken(t); closeAuth(); }}
            />
            <button className="close-btn" onClick={closeAuth}>×</button>
          </div>
        </div>
      )}
    </>
  );
}

export default App;
