import { useEffect, useMemo, useState } from "react";
import { askVideoQuestion, checkApi, processVideo } from "./api";

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  const paths = {
    logo: <><rect x="3" y="3" width="18" height="18" rx="5" /><path d="m10 8 6 4-6 4V8Z" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    video: <><rect x="3" y="5" width="18" height="14" rx="3" /><path d="m10 9 5 3-5 3V9Z" /></>,
    send: <><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></>,
    external: <><path d="M14 3h7v7M10 14 21 3" /><path d="M19 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    sparkle: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" /><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" /></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 0 4 22V5.5Z" /><path d="M4 6v16M8 7h8M8 11h8" /></>,
    chat: <><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8A8.5 8.5 0 0 1 8.7 3.9a8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    alert: <><path d="M10.3 3.9 2.6 17.2A2 2 0 0 0 4.3 20h15.4a2 2 0 0 0 1.7-2.8L13.7 3.9a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4M12 17h.01" /></>,
  };

  return <svg {...common}>{paths[name] || paths.sparkle}</svg>;
}

function formatTime(seconds = 0) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  if (hours) return `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

function getYouTubeId(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.endsWith("youtu.be")) return parsed.pathname.slice(1).split("/")[0];
    if (parsed.pathname === "/watch") return parsed.searchParams.get("v");
    const match = parsed.pathname.match(/^\/(?:shorts|embed|live)\/([^/]+)/);
    return match?.[1] || null;
  } catch {
    return null;
  }
}

function openTimestamp(videoUrl, start) {
  const id = getYouTubeId(videoUrl);
  if (!id) return;
  window.open(`https://www.youtube.com/watch?v=${id}&t=${Math.floor(start || 0)}s`, "_blank", "noopener,noreferrer");
}

function Sidebar({ onNewVideo, recentVideos, activeVideoId, onSelectRecent }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Icon name="logo" size={22} /></div>
        <div>
          <div className="brand-name">VideoMind AI</div>
          <div className="brand-subtitle">VIDEO LEARNING ASSISTANT</div>
        </div>
      </div>

      <button className="new-video-button" onClick={onNewVideo}>
        <Icon name="plus" size={17} /> <span>New video</span>
      </button>

      <div className="sidebar-label">RECENT VIDEOS</div>
      {recentVideos.length === 0 ? (
        <div className="sidebar-empty">Your analyzed videos will appear here.</div>
      ) : (
        <div className="recent-list">
          {recentVideos.map((video) => (
            <button
              key={video.video_id}
              className={`recent-item ${activeVideoId === video.video_id ? "active" : ""}`}
              onClick={() => onSelectRecent(video)}
              title={video.title || video.source_url}
            >
              <span className="recent-icon"><Icon name="video" size={16} /></span>
              <span className="recent-text">{video.title || video.source_url}</span>
            </button>
          ))}
        </div>
      )}

      <div className="sidebar-footer">
        <div className="avatar">V</div>
        <div className="footer-copy">
          <strong>Learning workspace</strong>
          <span>Local development</span>
        </div>
        <span className="status-dot" title="Local app" />
      </div>
    </aside>
  );
}

function EmptyWorkspace({ url, setUrl, onAnalyze, loading, error }) {
  return (
    <section className="empty-workspace">
      <div className="hero-icon"><Icon name="sparkle" size={30} /></div>
      <p className="eyebrow">YOUR PERSONAL VIDEO STUDY SPACE</p>
      <h1>Turn videos into <span>knowledge.</span></h1>
      <p className="hero-description">
        Explore a lecture, find the key ideas, and ask questions grounded in its transcript.
      </p>

      <form className="url-form" onSubmit={onAnalyze}>
        <div className="url-input-wrap">
          <span className="youtube-mark">▶</span>
          <input
            aria-label="YouTube video URL"
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="Paste a YouTube video link..."
            required
          />
        </div>
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? <span className="spinner" /> : <Icon name="sparkle" size={17} />}
          {loading ? "Analyzing..." : "Analyze video"}
        </button>
      </form>

      {error && <div className="error-banner"><Icon name="alert" size={18} /> <span>{error}</span></div>}

      <div className="steps-row">
        <div className="step-item"><span className="step-number">1</span><span>Extract transcript</span></div>
        <span className="step-divider" />
        <div className="step-item"><span className="step-number">2</span><span>Make it searchable</span></div>
        <span className="step-divider" />
        <div className="step-item"><span className="step-number">3</span><span>Ask questions</span></div>
      </div>
      <div className="privacy-note">Your workspace runs locally on your development machine.</div>
    </section>
  );
}

function ProcessingBanner({ loading }) {
  if (!loading) return null;
  return (
    <div className="processing-banner">
      <span className="spinner" />
      <div><strong>Preparing your video</strong><span>Extracting the transcript and building searchable sections. This may take a little while.</span></div>
    </div>
  );
}

function VideoHeader({ video, onNewVideo }) {
  return (
    <section className="video-header panel">
      <div className="video-thumbnail">
        <Icon name="video" size={28} />
        <span>YouTube video</span>
      </div>
      <div className="video-details">
        <div className="ready-label"><span className="status-dot" /> VIDEO READY</div>
        <h2>{video.title || "Your video is ready to explore"}</h2>
        <p>{video.transcript_segment_count ?? "—"} transcript segments <span className="dot-separator">•</span> {video.chunk_count ?? "—"} searchable sections</p>
        <div className="video-actions">
          <a className="subtle-button" href={video.source_url} target="_blank" rel="noreferrer">
            Watch on YouTube <Icon name="external" size={14} />
          </a>
          <button className="text-button" onClick={onNewVideo}>Analyze another</button>
        </div>
      </div>
    </section>
  );
}

function SummaryPanel() {
  return (
    <section className="panel summary-panel">
      <div className="section-heading">
        <div className="section-icon"><Icon name="book" size={18} /></div>
        <div><h3>Video summary</h3><p>Key ideas at a glance</p></div>
      </div>
      <div className="summary-notice">
        <Icon name="alert" size={19} />
        <div>
          <strong>Summary generation is not connected yet</strong>
          <p>The current backend extracts and indexes the transcript and supports grounded Q&amp;A. We can add a summary endpoint next.</p>
        </div>
      </div>
      <div className="summary-placeholder">
        <div className="placeholder-line wide" />
        <div className="placeholder-line" />
        <div className="placeholder-line medium" />
      </div>
      <div className="takeaways-heading">WHAT YOU'LL SEE HERE</div>
      <div className="takeaway-row"><span>01</span><p>A concise summary of the video's main idea</p></div>
      <div className="takeaway-row"><span>02</span><p>The most important takeaways and concepts</p></div>
    </section>
  );
}

function SourceCard({ source, videoUrl }) {
  return (
    <div className="source-card">
      <div className="source-time"><Icon name="clock" size={14} /> {formatTime(source.start)} – {formatTime(source.end)}</div>
      <p>{source.text}</p>
      <button className="source-link" onClick={() => openTimestamp(videoUrl, source.start)}>
        Jump to video <Icon name="external" size={13} />
      </button>
    </div>
  );
}

function AskPanel({ video, messages, onAsk, asking, question, setQuestion, error }) {
  return (
    <section className="panel ask-panel">
      <div className="section-heading">
        <div className="section-icon"><Icon name="chat" size={18} /></div>
        <div><h3>Ask AI</h3><p>Questions answered from this transcript</p></div>
        <span className="grounded-pill"><span className="status-dot" /> Transcript grounded</span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon"><Icon name="chat" size={23} /></div>
            <strong>What would you like to understand?</strong>
            <p>Ask about a concept, a specific moment, or the main ideas in this video.</p>
            <div className="suggested-questions">
              <button onClick={() => setQuestion("What are the main ideas explained in this video?")}>What are the main ideas?</button>
              <button onClick={() => setQuestion("Explain an important concept from this video.")}>Explain an important concept</button>
            </div>
          </div>
        )}
        {messages.map((message, index) => (
          <div className={`message ${message.role}`} key={`${index}-${message.question || message.content}`}>
            <div className="message-label">{message.role === "user" ? "YOU" : "VIDEOMIND AI"}</div>
            <div className="message-bubble">{message.content}</div>
            {message.sources?.length > 0 && (
              <div className="sources">
                <div className="sources-heading">SOURCES FROM THE VIDEO <span>{message.sources.length}</span></div>
                {message.sources.map((source, sourceIndex) => (
                  <SourceCard key={`${source.chunk_id}-${sourceIndex}`} source={source} videoUrl={video.source_url} />
                ))}
              </div>
            )}
          </div>
        ))}
        {asking && <div className="assistant-thinking"><span className="spinner" /> Finding relevant transcript sections...</div>}
      </div>

      {error && <div className="inline-error"><Icon name="alert" size={15} /> {error}</div>}
      <form className="question-form" onSubmit={onAsk}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask anything about this video..."
          rows={2}
          maxLength={2000}
          aria-label="Ask a question about the video"
        />
        <div className="question-form-footer">
          <span><Icon name="check" size={14} /> Answers use transcript excerpts</span>
          <button type="submit" className="primary-button ask-button" disabled={asking || !question.trim()}>
            {asking ? "Thinking..." : "Ask AI"} <Icon name="send" size={15} />
          </button>
        </div>
      </form>
    </section>
  );
}

export default function App() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [url, setUrl] = useState("");
  const [video, setVideo] = useState(null);
  const [recentVideos, setRecentVideos] = useState(() => {
    try { return JSON.parse(localStorage.getItem("videomind-recent") || "[]"); }
    catch { return []; }
  });
  const [loading, setLoading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const [messagesByVideo, setMessagesByVideo] = useState({});
  const [error, setError] = useState("");
  const [askError, setAskError] = useState("");

  useEffect(() => {
    checkApi()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }, []);

  const messages = useMemo(
    () => video ? messagesByVideo[video.video_id] || [] : [],
    [video, messagesByVideo]
  );

  function saveRecent(metadata) {
    const item = {
      ...metadata,
      title: metadata.title || metadata.source_url,
    };
    setRecentVideos((previous) => {
      const updated = [item, ...previous.filter((entry) => entry.video_id !== item.video_id)].slice(0, 8);
      localStorage.setItem("videomind-recent", JSON.stringify(updated));
      return updated;
    });
  }

  function resetWorkspace() {
    setVideo(null);
    setUrl("");
    setError("");
    setAskError("");
    setQuestion("");
  }

  async function handleAnalyze(event) {
    event.preventDefault();
    setError("");
    setAskError("");
    setLoading(true);
    try {
      const result = await processVideo(url.trim());
      const metadata = result.video || result;
      setVideo(metadata);
      setUrl(metadata.source_url || url.trim());
      saveRecent(metadata);
    } catch (err) {
      setError(err.message || "Video processing failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    if (!video || !question.trim()) return;
    const askedQuestion = question.trim();
    setAskError("");
    setQuestion("");
    setAsking(true);
    setMessagesByVideo((previous) => ({
      ...previous,
      [video.video_id]: [...(previous[video.video_id] || []), { role: "user", content: askedQuestion }],
    }));

    try {
      const result = await askVideoQuestion(video.video_id, askedQuestion, "Arabic");
      setMessagesByVideo((previous) => ({
        ...previous,
        [video.video_id]: [
          ...(previous[video.video_id] || []),
          { role: "assistant", content: result.answer, sources: result.sources || [] },
        ],
      }));
    } catch (err) {
      setAskError(err.message || "Could not answer this question.");
    } finally {
      setAsking(false);
    }
  }

  function selectRecent(item) {
    setVideo(item);
    setUrl(item.source_url || "");
    setError("");
    setAskError("");
  }

  return (
    <div className="app-shell">
      <Sidebar
        onNewVideo={resetWorkspace}
        recentVideos={recentVideos}
        activeVideoId={video?.video_id}
        onSelectRecent={selectRecent}
      />
      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{video ? "Video analysis" : "New video"}</strong></div>
          <div className={`api-status ${apiStatus}`}><span className="status-dot" /> API {apiStatus === "checking" ? "checking" : apiStatus === "online" ? "connected" : "offline"}</div>
        </header>

        <div className="page-content">
          {!video ? (
            <EmptyWorkspace url={url} setUrl={setUrl} onAnalyze={handleAnalyze} loading={loading} error={error} />
          ) : (
            <>
              <div className="workspace-title-row">
                <div><p className="eyebrow">VIDEO WORKSPACE</p><h1>Learn something new.</h1><p className="workspace-subtitle">Your video is indexed and ready for questions.</p></div>
                <button className="subtle-button new-analysis-top" onClick={resetWorkspace}><Icon name="plus" size={15} /> New video</button>
              </div>
              <ProcessingBanner loading={loading} />
              <VideoHeader video={video} onNewVideo={resetWorkspace} />
              <div className="content-grid">
                <SummaryPanel />
                <AskPanel
                  video={video}
                  messages={messages}
                  onAsk={handleAsk}
                  asking={asking}
                  question={question}
                  setQuestion={setQuestion}
                  error={askError}
                />
              </div>
            </>
          )}
        </div>
        <footer className="app-footer">VideoMind AI <span>•</span> Learn from videos, one question at a time.</footer>
      </main>
    </div>
  );
}