
require("dotenv").config();

const express = require("express");
const cors = require("cors");

const chatRoutes = require("./routes/chatRoutes");
const documentRoutes = require("./routes/documentRoutes");

const app = express();

const PORT = process.env.PORT || 5000;


// Middleware configuration
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));


// Root endpoint
app.get("/", (req, res) => {
    res.status(200).json({
        message: "Welcome to Conversational RAG Backend",
        status: "running",
        version: "1.0.0"
    });
});


// Health check endpoint
app.get("/api/health", (req, res) => {
    res.status(200).json({
        status: "healthy",
        service: "Conversational RAG Node.js Backend"
    });
});


// Chat API route
app.use("/api/chat", chatRoutes);


// Document upload API route
app.use("/api/documents", documentRoutes);


// Handle unknown routes
app.use((req, res) => {
    res.status(404).json({
        message: `Route ${req.method} ${req.originalUrl} not found`
    });
});


// Global error handler
app.use((err, req, res, next) => {
    console.error("Backend Error:", err);

    res.status(err.statusCode || 500).json({
        message: err.message || "Internal server error"
    });
});


// Start Express server
app.listen(PORT, () => {
    console.log("--------------------------------------");
    console.log("Conversational RAG Backend");
    console.log("--------------------------------------");
    console.log(`Server running at: http://localhost:${PORT}`);
    console.log("Status: Ready");
    console.log("--------------------------------------");
});
