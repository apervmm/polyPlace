# poly/Place is a real-time and multiplayer game inspired by r/Place.

***Prod:*** https://pplace.vercel.app/ 

## Architecture:
- ***Auth Server:*** The Auth server is an ExpressJS REST API that handles two POST requests using JWT: /login and /register. The package is hosted on Vercel.

- ***Client:*** It's a React client-side application that manages the UI/UX. The client listens to the authentication server ***auth-server*** and the WebSocket server ***server*** to handle the canvas board using createImageData(). The package is hosted on Vercel.

- ***Server:*** A NodeJS server manages websockets (bidirectional HTTP requests) between connected users. Newly connected users fetch the recently updated pixels on the board from the event-based database. When the client writes a new event into the database (places a pixel on the board), the server broadcasts the update to all listening (connected) users.



## Running on Localhost:
1. Fork the Main repository
2. Create an account on Supabase: https://supabase.com/
3. In SQL Editor, run the following queries:
   ```
   CREATE TABLE IF NOT EXISTS users (
       userid UUID PRIMARY KEY,
       username TEXT NOT NULL UNIQUE,
       password TEXT NOT NULL,
       email TEXT NOT NULL UNIQUE,
       registertime TIMESTAMPTZ DEFAULT now()
   );
   
   
   CREATE TABLE IF NOT EXISTS actions (
       id SERIAL PRIMARY KEY,
       coordinate TEXT NOT NULL,
       color TEXT NOT NULL,
       userid UUID NOT NULL,
       timestamp TIMESTAMPTZ DEFAULT now(),
       CONSTRAINT fk_userid
           FOREIGN KEY (userid)
           REFERENCES users (userid)
           ON DELETE CASCADE
           ON UPDATE CASCADE
   );
   ```
3. In ***Supabase*** account click on coonect and copy ***Transiaction Pooler***
4. In ***server*** package, create .env file and add:
```
SUPABASE_URL=<add supabase url from settings>
SUPABASE_SECRET_KEY=<add sectet key>
SUPABASE_ANON=<add anon key from settings>
DATABASE_URL=<add transaction pooler>
```

6. In ***auth*** package, create .env file and add:
```
SUPABASE_URL=<add supabase url from settings>
SUPABASE_SECRET_KEY=<add sectet key>
SUPABASE_ANON=<add anon key from settings>
DATABASE_URL=<add transaction pooler>
JWT_SECRET=<add any key>
JWT_EXPIRES_IN=1d
```
   
7. In root foleder, execute:
```
npm install
```
8. In the **auth-server** package, execute:
```
node auth.js
```
This starts the auth-server at [http://localhost:3000/](http://localhost:3000/). Keep it running in a separate terminal.
   
9. Then, in the **server** package, execute:
```
node server.js
```
   This starts your WebSocket server [ws://127.0.0.1:8765/](ws://127.0.0.1:8765/). Keep it running in a separate terminal.
   

   
10. In the **client** package, execute:
```
npm run dev
```
This should take you to [http://127.0.0.1:8080/](http://127.0.0.1:5173/), where the app will be running.

Note: In development, make sure to replace the fetching APIs as needed.


11. When commiting changes, please make sure to gitignore ***/dist***, ***.env***, ***node_modules***, and all other private folders/files






