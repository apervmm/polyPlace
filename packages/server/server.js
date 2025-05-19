import { WebSocketServer } from 'ws';
import http from 'http';
import url from 'url';
import jwt from 'jsonwebtoken';
import sql from './db.js';
import 'dotenv/config';
import express from 'express';
import cors from 'cors';

const app = express();



app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
    res.status(200).send('OK');
  });

const server = http.createServer(app);
const wsServer = new WebSocketServer({ server });
const port = process.env.PORT || 8080;


async function testConnection() {
    try {
        const [{ now }] = await sql`SELECT now()`;
        console.log("Connected to Supabase:", now);
    } catch (err) {
        console.error("Error connecting to DB:", err);
    }
}



async function getState() {
    const rows = await sql`
        SELECT DISTINCT ON (x, y)
            x, y, color, timestamp, userid
        FROM actions
        ORDER BY x, y, timestamp DESC`;
    // console.log(rows);
    return rows;
}



async function insertAction(x, y, color, userId) {
    const [row] = await sql`
        INSERT INTO actions (x, y, color, userid)
        VALUES (${x}, ${y}, ${color}, ${userId})
        RETURNING *`;
    console.log("Inserted into action:", row);
    return row;
}


function broadcast(wsServer, payload) {
    const msgString = JSON.stringify(payload);
    wsServer.clients.forEach((client) => {
        if (client.readyState === client.OPEN) {
            client.send(msgString);
        }
    });
}


async function handlePlace(wsServer, data, userId) {
    const { x, y, color } = data;

    const event = {
        type: "update",
        x, y,
        color,
        userId,
        timestamp: new Date().toISOString()
    };


    await insertAction(x, y, color, userId);
    broadcast(wsServer, event);
}


wsServer.on("connection", async (connection, request) => {
    const { token } = url.parse(request.url, true).query;

    // if (!token) {
    //     connection.send(JSON.stringify({ error: "No token provided" }));
    //     connection.close();
    //     return;
    // }

    let userId = null; 

    // try {
    //     const decoded = jwt.verify(token, process.env.JWT_SECRET);
    //     userId = decoded.userId; 
    //     // console.log("Decoded JWT:", decoded);
    // } catch (err) {
    //     console.error("JWT verification failed:", err);
    //     connection.send(JSON.stringify({ error: "Invalid token" }));
    //     connection.close();
    //     return;
    // }

    if (token) {
        try {
            const decoded = jwt.verify(token, process.env.JWT_SECRET);
            userId = decoded.userId;
        } catch (err) {
            console.error("JWT verification failed:", err);
        }
    }

    console.log(`New client ${userId ? "userId="+userId : "(guest)"}`);

    // console.log(`New client userId=${userId}`);

    const pixelState = await getState();
    connection.send(JSON.stringify({
        type: "init",
        pixels: pixelState,
        userId
    }));


    connection.on("message", async (msg) => {
        try {
            const data = JSON.parse(msg);
            if (data.type === "place") {
                await handlePlace(wsServer, data, userId);
            }
        } catch (err) {
            console.error("Error parsing message:", err);
        }
    });



    connection.on("close", () => {
        console.log(`Client with userId=${userId} disconnected`);
    });
});


async function startServer() {
    server.listen(port, '0.0.0.0', () => {
        console.log(`Server running on ${port}`);
    });
    await testConnection();
}

startServer();