
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function ChatMessage({ role, content, sources = [] }) {
  const isAssistant = role === "assistant";

  const safeContent =
    typeof content === "string" ? content : "";

  const formattedContent = safeContent.replace(
    /\\+([*_`~])/g,
    "$1"
  );

  return (
    <div
      className={`mb-5 flex w-full ${
        isAssistant ? "justify-start" : "justify-end"
      }`}
    >
      <div
        className={`max-w-[90%] rounded-2xl px-5 py-3 ${
          isAssistant
            ? "bg-slate-100 text-slate-800"
            : "bg-blue-600 text-white"
        }`}
      >
        <p className="mb-2 text-xs font-semibold opacity-70">
          {isAssistant ? "AI Assistant" : "You"}
        </p>

        {isAssistant ? (
          <>
            <div className="break-words text-sm leading-7">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {formattedContent}
              </ReactMarkdown>
            </div>

            {sources.length > 0 && (
              <div className="mt-4 border-t border-slate-300 pt-3">
                <p className="mb-2 text-xs font-bold text-slate-600">
                  Sources:
                </p>

                <ul className="list-disc space-y-1 pl-5 text-xs text-slate-600">
                  {sources.map((source, index) => {
                    const sourceName =
                      typeof source === "string"
                        ? source
                        : source.source ||
                          source.filename ||
                          "Document";

                    return (
                      <li key={index}>
                        {sourceName}
                        {source.page
                          ? ` (Page ${source.page})`
                          : ""}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p className="whitespace-pre-wrap break-words text-sm leading-6">
            {safeContent}
          </p>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
