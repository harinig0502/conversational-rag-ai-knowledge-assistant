
import { useState } from "react";
import api from "../services/api";
import ChatMessage from "./ChatMessage";
import DocumentUpload from "./DocumentUpload";

function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();

    const userQuestion = String(question || "").trim();

    if (!userQuestion || isLoading) {
      return;
    }

    // Add the user's message
    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "user",
        content: userQuestion,
      },
    ]);

    setQuestion("");
    setIsLoading(true);

    try {
      const response = await api.post("/chat", {
        question: userQuestion,
        top_k: 5,
        ...(conversationId !== null
          ? { conversation_id: conversationId }
          : {}),
      });

      const assistantAnswer =
        typeof response.data?.answer === "string"
          ? response.data.answer
          : "The AI service returned no answer.";

      if (response.data?.conversation_id != null) {
        setConversationId(response.data.conversation_id);
      }

      // Add the AI response
      setMessages((previousMessages) => [
        ...previousMessages,
        {
          role: "assistant",
          content: assistantAnswer,
        },
      ]);

    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Unable to connect to the backend. Please check your services.";

      setMessages((previousMessages) => [
        ...previousMessages,
        {
          role: "assistant",
          content: `Error: ${errorMessage}`,
        },
      ]);

    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">

      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <h1 className="text-xl font-bold text-slate-800">
          Conversational RAG
        </h1>
        <p className="text-sm text-slate-500">
          AI Knowledge Assistant
        </p>
      </header>

      <main className="mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 gap-6 px-4 py-6 lg:grid-cols-[320px_minmax(0,1fr)]">

        <aside>
          <DocumentUpload />
        </aside>

        <section className="flex min-h-[600px] flex-col rounded-xl border border-slate-200 bg-white shadow-sm">

          <div className="border-b px-5 py-4">
            <h2 className="font-bold text-slate-800">
              Chat with your documents
            </h2>
            <p className="text-sm text-slate-500">
              Ask questions about your knowledge base.
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-5">

            {messages.length === 0 ? (
              <div className="flex min-h-64 h-full flex-col items-center justify-center text-center">
                <h2 className="text-2xl font-bold text-slate-800">
                  How can I help you?
                </h2>

                <p className="mt-3 max-w-md text-slate-500">
                  Upload your documents and ask questions.
                  Your AI Knowledge Assistant will retrieve
                  relevant information and generate answers.
                </p>
              </div>
            ) : (
              messages.map((message, index) => {
                const messageContent =
                  message.content ??
                  message.text ??
                  message.answer ??
                  message.message ??
                  "No message content was returned.";

                return (
                 <ChatMessage
  key={index}
  role={message.role}
  content={String(messageContent)}
  sources={message.sources || []}
/>
                );
              })
            )}

            {isLoading && (
              <p className="mb-4 text-sm text-slate-500">
                AI Assistant is thinking...
              </p>
            )}

          </div>

          <form
            onSubmit={handleSubmit}
            className="flex gap-3 border-t bg-white p-3"
          >
            <input
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask something about your documents..."
              maxLength={2000}
              disabled={isLoading}
              className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
            />

            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? "Sending..." : "Send"}
            </button>
          </form>

        </section>
      </main>
    </div>
  );
}

export default ChatWindow;
