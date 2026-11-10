
const mysql = require("mysql2/promise");

// Create a connection pool for MySQL
const pool = mysql.createPool({
    host: process.env.DB_HOST || "localhost",
    user: process.env.DB_USER || "root",
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME || "conversational_rag",

    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Export the connection pool
module.exports = pool;
