
const axios = require("axios");

// Python FastAPI service URL
const AI_SERVICE_URL =
    process.env.AI_SERVICE_URL || "http://127.0.0.1:8000";


// Send a question to the Python RAG service
async function getAIAnswer(question, topK = 5) {

    try {

        const response = await axios.post(
            `${AI_SERVICE_URL}/chat`,
            {
                question: question,
                top_k: topK
            },
            {
                timeout: 120000
            }
        );

        return response.data;

    } catch (error) {

        if (error.response) {

            const serviceError = new Error(
                error.response.data?.detail ||
                "The AI service returned an error."
            );

            serviceError.statusCode = 502;

            throw serviceError;
        }

        const connectionError = new Error(
            `Unable to connect to the AI service at ${AI_SERVICE_URL}. Check whether FastAPI is running.`
        );

        connectionError.statusCode = 503;

        throw connectionError;
    }
}


// Upload a document to the Python RAG service
async function uploadDocument(file) {

    try {

        // Create multipart form data
        const formData = new FormData();

        // Convert uploaded file buffer into a Blob
        const documentBlob = new Blob(
            [file.buffer],
            {
                type: file.mimetype
            }
        );

        // Attach the document with its original filename
        formData.append(
            "file",
            documentBlob,
            file.originalname
        );


        // Forward the document to FastAPI
        const response = await axios.post(
            `${AI_SERVICE_URL}/documents/upload`,
            formData,
            {
                timeout: 120000
            }
        );

        return response.data;

    } catch (error) {

        if (error.response) {

            const serviceError = new Error(
                error.response.data?.detail ||
                "The AI service could not upload the document."
            );

            serviceError.statusCode = 502;

            throw serviceError;
        }

        const connectionError = new Error(
            `Unable to connect to the AI service at ${AI_SERVICE_URL}.`
        );

        connectionError.statusCode = 503;

        throw connectionError;
    }
}


// Export both functions
module.exports = {
    getAIAnswer,
    uploadDocument
};
