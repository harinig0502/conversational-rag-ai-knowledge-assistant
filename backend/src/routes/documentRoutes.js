
const express = require("express");

const { upload } = require("../controllers/documentController");
const { upload: uploadMiddleware } = require("../middleware/uploadMiddleware");

const router = express.Router();


// POST /api/documents/upload
router.post(
    "/upload",
    uploadMiddleware.single("file"),
    upload
);


// Export router
module.exports = router;
