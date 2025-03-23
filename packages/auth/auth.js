import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import sql from './db.js'; 
import 'dotenv/config';
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());


app.get('/', (req, res) => {
    res.status(200).send('Auth-server is running.');
});

app.post('/register', async (req, res) => {
    try {
        const { username, password, email } = req.body;

        console.log('userbody:', username);
        if (!username || !password || !email) {
            return res.status(400).json({ success: false, error: 'Missing fields' });
        }


        const userId = uuidv4();
        const hashedPassword = await bcrypt.hash(password, 10);

        const [row] = await sql`
            INSERT INTO users (userid, username, password, email)
            VALUES (${userId}, ${username}, ${hashedPassword}, ${email})
            RETURNING userid, username, email, registertime`;


        res.json({ success: true, user: row });
    } catch (err) {
        console.error('Registering Error:', err);
        res.status(500).json({ success: false, error: 'Registration failed' });
    }
});




app.post('/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        if (!username || !password) {
            return res.status(400).json({ success: false, error: 'Missing username or password' });
        }

        const [user] = await sql`
            SELECT userid, username, password
            FROM users
            WHERE username = ${username}`;


        if (!user) {
            return res.status(401).json({ success: false, error: 'User not found' });
        }

        const match = await bcrypt.compare(password, user.password);
        if (!match) {
            return res.status(401).json({ success: false, error: 'Invalid login/password' });
        }

        const token = jwt.sign(
            { userId: user.userid },      
            process.env.JWT_SECRET,       
            { expiresIn: `${process.env.JWT_EXPIRES_IN}`}   
        );

        res.json({ success: true, token });
    } catch (err) {
        console.error('Error logging in:', err);
        res.status(500).json({ success: false, error: 'Login failed' });
    }
});




const authPort = process.env.AUTH_PORT || process.env.PORT || 3000;
app.listen(authPort, () => {
    console.log(`Auth-server running on http://localhost:${authPort}/`);
});
