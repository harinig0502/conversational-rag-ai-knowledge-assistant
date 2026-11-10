
const multer = require("multer");
const path = require("path");

// Allowed document extensions
const allowedExtensions = [".pdf", ".docx", ".txt"];


// Store uploaded files temporarily in memory
const storage = multer.memoryStorage();


// Validate uploaded file type
function fileFilter(req, file, callback) {

    const extension = path.extname(file.originalname).toLowerCase();

    if (!allowedExtensions.includes(extension)) {

        return callback(
            new Error("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")
        );

    }

    callback(null, true);
}


// Configure Multer
const upload = multer({

    storage: storage,

    fileFilter: fileFilter,

    limits: {
        fileSize: 10 * 1024 * 1024
    }

});


// Export upload middleware
module.exports = {
    upload
};
