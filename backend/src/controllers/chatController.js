
const { getAIAnswer } = require("../services/aiService");
const pool = require("../config/database");

// Handle chat requests
async function chat(req, res, next) {
    try {
        const {
            question,
            top_k: topK = 5,
            conversation_id: conversationId
        } = req.body || {};

        // Validate the question
        if (
            typeof question !== "string" ||
            question.trim().length === 0
        ) {
            return res.status(400).json({
                message: "Please provide a valid question."
            });
        }

        if (question.trim().length > 2000) {
            return res.status(400).json({
                message: "Question cannot exceed 2000 characters."
            });
        }

        // Validate top_k
        if (
            !Number.isInteger(topK) ||
            topK < 1 ||
            topK > 10
        ) {
            return res.status(400).json({
                message: "top_k must be an integer between 1 and 10."
            });
        }

        // Validate an existing conversation ID, if provided
        if (
            conversationId !== undefined &&
            conversationId !== null &&
            (!Number.isSafeInteger(conversationId) || conversationId <= 0)
        ) {
            return res.status(400).json({
                message: "Invalid conversation_id."
            });
        }

        let currentConversationId = conversationId;

        if (currentConversationId !== undefined &&
            currentConversationId !== null) {

            const [existingConversation] = await pool.execute(
                "SELECT id FROM conversations WHERE id = ?",
                [currentConversationId]
            );

            if (existingConversation.length === 0) {
                return res.status(404).json({
                    message: "Conversation not found."
                });
            }
        }

        // Generate the AI answer
        const result = await getAIAnswer(
            question.trim(),
            topK
        );

        // Create a new conversation if one was not supplied
        if (
            currentConversationId === undefined ||
            currentConversationId === null
        ) {
            const title = question.trim().slice(0, 80);

            const [conversationResult] = await pool.execute(
                "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
                [null, title]
            );

            currentConversationId = conversationResult.insertId;
        }

        // Save the user's message
        await pool.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            [
                currentConversationId,
                "user",
                question.trim()
            ]
        );

        // Save the AI assistant's answer
        await pool.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            [
                currentConversationId,
                "assistant",
                result.answer
            ]
        );

        // Return the answer and conversation ID
        return res.status(200).json({
            ...result,
            conversation_id: currentConversationId
        });

    } catch (error) {
        next(error);
    }
}

// Export controller
module.exports = {
    chat
};
