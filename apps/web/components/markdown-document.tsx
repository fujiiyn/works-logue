import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownDocumentProps {
  content: string;
}

const EXTERNAL_HREF = /^(https?:)?\/\//i;

export function MarkdownDocument({ content }: MarkdownDocumentProps) {
  return (
    <div data-testid="markdown-document">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h2 className="mt-8 mb-3 border-b border-border pb-1 text-heading-l text-primary-dark">
              {children}
            </h2>
          ),
          h2: ({ children }) => (
            <h3 className="mt-6 mb-2 text-heading-m text-primary-dark">
              {children}
            </h3>
          ),
          h3: ({ children }) => (
            <h4 className="mt-4 mb-2 text-body-m font-bold text-primary-dark">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="mb-4 text-body-m leading-[1.8] text-primary-dark">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 ml-5 list-disc space-y-1 text-body-m leading-[1.8] text-primary-dark">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 ml-5 list-decimal space-y-1 text-body-m leading-[1.8] text-primary-dark">
              {children}
            </ol>
          ),
          a: ({ children, href }) => {
            const isExternal = !!href && EXTERNAL_HREF.test(href);
            return (
              <a
                href={href}
                className="text-primary underline hover:text-primary-dark"
                target={isExternal ? "_blank" : undefined}
                rel={isExternal ? "noopener noreferrer" : undefined}
              >
                {children}
              </a>
            );
          },
          blockquote: ({ children }) => (
            <blockquote className="my-4 border-l-2 border-primary pl-4 text-body-m leading-[1.8] text-text-secondary">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-6 border-0 border-t border-border" />,
          strong: ({ children }) => (
            <strong className="font-bold text-primary-dark">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto">
              <table className="w-full border-collapse border border-border text-body-s">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-bg-card">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="border border-border px-3 py-2 text-left font-bold text-primary-dark">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-3 py-2 align-top leading-[1.7] text-primary-dark">
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
