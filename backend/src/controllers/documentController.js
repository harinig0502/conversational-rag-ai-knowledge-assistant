
const path = require("path");

const { uploadDocument } = require("../services/aiService");
const pool = require("../config/database");

// Handle document upload requests
async function upload(req, res, next) {
    try {
        if (!req.file) {
            return res.status(400).json({
                message: "Please select a document to upload."
            });
        }

        // Send the document to the Python RAG service
        const result = await uploadDocument(req.file);

        // Extract the document extension
        const fileType = path
            .extname(req.file.originalname)
            .replace(".", "")
            .toLowerCase();

        // Save document information in MySQL
        const [dbResult] = await pool.execute(
            `INSERT INTO documents
            (user_id, original_filename, file_type, file_size_bytes,
             chunks_indexed, status)
            VALUES (?, ?, ?, ?, ?, 'indexed')`,
            [
                null,
                req.file.originalname,
                fileType,
                req.file.size,
                result.chunks_indexed || 0
            ]
        );

        // Return the upload result
        return res.status(200).json({
            ...result,
            document_id: dbResult.insertId,
            database_status: "saved"
        });

    } catch (error) {
        next(error);
    }
}

// Export controller
module.exports = {
    upload
};
