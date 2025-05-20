### polyPlace is a real-time and multiplayer game inspired by r/Place.

***Prod:*** https://poly-place-client.vercel.app/ 

### Packages:
- ***Auth Server:*** The Auth server is an ExpressJS REST API that handles two POST requests using JWT: /login and /register. The package is hosted on Vercel.

- ***Client:*** It's a React client-side application that manages the UI/UX. The client listens to the authentication server ***auth-server*** and the WebSocket server ***server*** to handle the canvas board using createImageData(). The package is hosted on Vercel.

- ***Server:*** A NodeJS server that manages websockets (bidirectional HTTP requests) between connected users. Newly connected users fetch the recently updated pixels on the board from the event-based database. When the client writes a new event into the database (places a pixel on the board), the server broadcasts the update to all listening (connected) users. 



