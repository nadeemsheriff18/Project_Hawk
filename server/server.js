// server.js
import express from 'express';
import { MongoClient } from 'mongodb';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import cors from 'cors';

const app = express();
app.use(cors());
app.use(express.json());

// Connection URL and Database Name
const uri = 'mongodb+srv://nadeemsheriff18:nadeem01@database.qnufz.mongodb.net/?retryWrites=true&w=majority&appName=Database';
const client = new MongoClient(uri);
const dbName = 'Database';

let db;

// Connect to the database
async function connectToDatabase() {
  try {
    await client.connect();
    db = client.db(dbName);
    console.log('Connected successfully to MongoDB');
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
  }
}

// Call the connectToDatabase function
connectToDatabase();

// Register route
app.post('/register', async (req, res) => {
  const { username, password } = req.body;
  try {
    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = { username, password: hashedPassword };
    const collection = db.collection('users');
    await collection.insertOne(newUser);
    res.status(201).send('User registered');
  } catch (error) {
    res.status(400).send('Error registering user');
  }
});

// Login route
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const collection = db.collection('users');
    const user = await collection.findOne({ username });
    if (!user) return res.status(400).send('User not found');

    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) return res.status(400).send('Invalid password');

    const token = jwt.sign({ id: user._id }, 'yourSecretKey');
    res.status(200).json({ token });
  } catch (error) {
    res.status(500).send('Error logging in');
  }
});

// Endpoint to get alerts from MongoDB
app.get('/alerts', async (req, res) => {
  try {
    const alerts = await db.collection('alerts').find({}).toArray();
    res.json(alerts);
  } catch (error) {
    console.error('Error fetching alerts:', error);
    res.status(500).send('Error fetching alerts');
  }
});



// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
