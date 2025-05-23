### poly/Place is a real-time and multiplayer game inspired by r/Place.

***Prod:*** https://poly-place-client.vercel.app/ 

### Packages:
- ***Auth Server:*** The Auth server is an ExpressJS REST API that handles two POST requests using JWT: /login and /register. The package is hosted on Vercel.

- ***Client:*** It's a React client-side application that manages the UI/UX. The client listens to the authentication server ***auth-server*** and the WebSocket server ***server*** to handle the canvas board using createImageData(). The package is hosted on Vercel.

- ***Server:*** A NodeJS server that manages websockets (bidirectional HTTP requests) between connected users. Newly connected users fetch the recently updated pixels on the board from the event-based database. When the client writes a new event into the database (places a pixel on the board), the server broadcasts the update to all listening (connected) users.



### Develpment:

1. In the **auth-server** package, execute:

   ```
   node auth.js
   ```

   This starts the auth-server at [http://localhost:3000/](http://localhost:3000/). Keep it running in a separate terminal.

2. Then, in the **server** package, execute:
   ```
   node server.js
   ```
   This starts your WebSocket server [ws://127.0.0.1:8765/](ws://127.0.0.1:8765/). Keep it running in a separate terminal.
   
4. In the **client** package, execute:
   ```
   npm run dev
   ```
   This should take you to [http://127.0.0.1:8080/](http://127.0.0.1:5173/), where the the app will be running.


   Note: In development, make sure to replace the fetching APIs as needed. 






