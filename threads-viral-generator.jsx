import { useState } from "react";

const CATEGORIES = [
  { id: "all", label: "🌐 Semua", desc: "Trending apapun hari ini" },
  { id: "tech", label: "💻 Teknologi", desc: "AI, gadget, apps viral" },
  { id: "lifestyle", label: "✨ Lifestyle", desc: "Tren hidup, kesehatan, produktivitas" },
  { id: "sosial", label: "🔥 Sosial", desc: "Isu, drama, opini viral" },
  { id: "hiburan", label: "🎬 Hiburan", desc: "Film, musik, konten viral" },
];

export default function App() {
  const [affiliateLink, setAffiliateLink] = useState("");
  const [category, setCategory] = useState("all");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState("idle");
  const [copiedIdx, setCopiedIdx] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [savedLink, setSavedLink] = useState("");

  const handleGenerate = async () => {
    const linkToUse = affiliateLink.trim() || savedLink;
    setLoading(true);
    setResult(null);
    setCopiedIdx(null);

    const catLabel = CATEGORIES.find(c => c.id === category)?.desc || "semua topik";
    setStep("searching");

    const searchPrompt = `Kamu adalah social media strategist Indonesia yang ahli bikin konten viral di Threads.

Tugasmu:
1. Cari topik yang SEDANG VIRAL / TRENDING di Indonesia hari ini (${new Date().toLocaleDateString("id-ID", {day:"numeric",month:"long",year:"numeric"})})
2. Pilih 1 topik paling rame dari kategori: ${catLabel}
3. Buat konten Threads dalam format THREAD BERSAMBUNG (seperti Twitter/X thread) — pecah jadi 4-6 bagian pendek terpisah
4. Bagian terakhir WAJIB berisi CTA affiliate yang natural

PENTING untuk format slide/bagian:
- Setiap bagian MAKSIMAL 3-4 kalimat pendek
- Setiap bagian berdiri sendiri tapi nyambung ke bagian berikutnya
- Bagian 1: Hook kuat, bikin orang penasaran
- Bagian 2-4: Isi / opini / cerita
- Bagian terakhir sebelum affiliate: ajak diskusi / tanya pendapat
- Bagian affiliate: natural, bukan hard sell

Format output HANYA JSON tanpa markdown:
{
  "topik": "judul topik trending yang dipilih",
  "kenapa_viral": "1 kalimat singkat kenapa topik ini lagi rame",
  "slides": [
    "teks bagian 1 (hook, max 3 kalimat, ada emoji)",
    "teks bagian 2 (max 3-4 kalimat, ada emoji)",
    "teks bagian 3 (max 3-4 kalimat, ada emoji)",
    "teks bagian 4 (max 3-4 kalimat, ada emoji, ajak diskusi)",
    "btw yang lagi cari HP baru, gue nemuin deals bagus banget nih 👇\\n🛒 ${linkToUse || 'shopee.co.id/affiliate-link-kamu'}"
  ],
  "hook_score": "angka 1-10 seberapa kuat hook pembukanya",
  "prediksi_engagement": "prediksi singkat kenapa konten ini bakal rame di Threads"
}`;

    try {
      setStep("writing");
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1500,
          tools: [{ type: "web_search_20250305", name: "web_search" }],
          messages: [{ role: "user", content: searchPrompt }],
        }),
      });

      const data = await response.json();
      const text = data.content
        .map(i => i.type === "text" ? i.text : "")
        .filter(Boolean)
        .join("\n");

      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (!jsonMatch) throw new Error("No JSON");
      const parsed = JSON.parse(jsonMatch[0]);
      setResult(parsed);
      if (linkToUse) setSavedLink(linkToUse);
    } catch (err) {
      setResult({ error: true });
    }

    setStep("idle");
    setLoading(false);
  };

  const handleCopySlide = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const handleCopyAll = () => {
    if (!result?.slides) return;
    navigator.clipboard.writeText(result.slides.join("\n\n---\n\n"));
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  const scoreColor = (s) => {
    const n = parseInt(s);
    if (n >= 8) return "#4ade80";
    if (n >= 6) return "#fbbf24";
    return "#f87171";
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0a",
      fontFamily: "'DM Sans', sans-serif",
      color: "#fff",
      padding: "20px 16px 40px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;0,900;1,400&family=Instrument+Serif:ital@0;1&display=swap');
        * { box-sizing: border-box; }
        ::placeholder { color: #444 !important; }
        .cat-btn:hover { border-color: rgba(255,255,255,0.3) !important; }
        .gen-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 30px rgba(255,255,255,0.15); }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;0,900;1,400&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet" />

      <div style={{ maxWidth: "540px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ marginBottom: "32px", paddingTop: "8px" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: "6px",
            background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "20px", padding: "4px 12px", fontSize: "11px", color: "#888",
            marginBottom: "16px", letterSpacing: "1px", textTransform: "uppercase",
          }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#4ade80", animation: "pulse 2s infinite" }} />
            Trend Hijacking · Threads
          </div>
          <h1 style={{
            fontSize: "clamp(28px, 7vw, 42px)", fontFamily: "'Instrument Serif', serif",
            fontWeight: 400, lineHeight: 1.1, margin: "0 0 10px",
          }}>
            Konten viral,<br />
            <em style={{ color: "#888" }}>affiliate tetap jalan.</em>
          </h1>
          <p style={{ color: "#555", fontSize: "14px", margin: 0, lineHeight: 1.6 }}>
            AI cari topik trending hari ini → bikin konten Threads yang rame → link affiliate nyempil natural di bawah.
          </p>
        </div>

        {/* Affiliate Link Input */}
        <div style={{ marginBottom: "20px" }}>
          <label style={{ fontSize: "11px", color: "#555", fontWeight: 500, letterSpacing: "1px", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
            Link Affiliate Shopee kamu
          </label>
          <input
            value={affiliateLink}
            onChange={e => setAffiliateLink(e.target.value)}
            placeholder="https://shopee.co.id/..."
            style={{
              width: "100%", padding: "13px 16px", borderRadius: "10px",
              border: "1px solid #222", background: "#111",
              color: "#fff", fontSize: "14px", outline: "none", fontFamily: "inherit",
            }}
          />
          <p style={{ fontSize: "11px", color: "#444", marginTop: "6px" }}>
            Kosongkan dulu kalau belum punya, bisa diisi nanti
          </p>
        </div>

        {/* Category */}
        <div style={{ marginBottom: "24px" }}>
          <label style={{ fontSize: "11px", color: "#555", fontWeight: 500, letterSpacing: "1px", textTransform: "uppercase", display: "block", marginBottom: "10px" }}>
            Kategori Trending
          </label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {CATEGORIES.map(c => (
              <button key={c.id} className="cat-btn" onClick={() => setCategory(c.id)} style={{
                padding: "8px 14px", borderRadius: "8px", cursor: "pointer",
                border: category === c.id ? "1px solid #fff" : "1px solid #222",
                background: category === c.id ? "#fff" : "#111",
                color: category === c.id ? "#000" : "#666",
                fontSize: "13px", fontFamily: "inherit", fontWeight: category === c.id ? 700 : 400,
                transition: "all 0.15s",
              }}>
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <button
          className="gen-btn"
          onClick={handleGenerate}
          disabled={loading}
          style={{
            width: "100%", padding: "16px", borderRadius: "10px", border: "none",
            background: loading ? "#1a1a1a" : "#fff",
            color: loading ? "#444" : "#000",
            fontSize: "15px", fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
            fontFamily: "inherit", transition: "all 0.2s", marginBottom: "28px",
          }}
        >
          {loading ? (
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}>
              <span style={{ width: "16px", height: "16px", border: "2px solid #333", borderTop: "2px solid #666", borderRadius: "50%", animation: "spin 0.8s linear infinite", display: "inline-block" }} />
              {step === "searching" ? "Nyari topik trending..." : "Nulis konten..."}
            </span>
          ) : "⚡ Generate Konten Viral"}
        </button>

        {/* Result */}
        {result && !result.error && (
          <div style={{ animation: "fadeUp 0.4s ease" }}>

            {/* Trending badge + hook score */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px", marginBottom: "14px" }}>
              <div>
                <div style={{ fontSize: "11px", color: "#555", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>🔥 Topik Trending</div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "#fff" }}>{result.topik}</div>
                <div style={{ fontSize: "13px", color: "#666", marginTop: "4px" }}>{result.kenapa_viral}</div>
              </div>
              <div style={{
                minWidth: "56px", height: "56px", borderRadius: "10px",
                border: `2px solid ${scoreColor(result.hook_score)}`,
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flexShrink: 0,
              }}>
                <div style={{ fontSize: "20px", fontWeight: 900, color: scoreColor(result.hook_score), lineHeight: 1 }}>{result.hook_score}</div>
                <div style={{ fontSize: "9px", color: "#555", textTransform: "uppercase", letterSpacing: "0.5px" }}>hook</div>
              </div>
            </div>

            {/* Prediksi */}
            <div style={{
              padding: "12px 14px", borderRadius: "8px",
              background: "rgba(74,222,128,0.07)", border: "1px solid rgba(74,222,128,0.15)",
              fontSize: "13px", color: "#4ade80", marginBottom: "20px", lineHeight: 1.5,
            }}>
              💡 {result.prediksi_engagement}
            </div>

            {/* Header slides */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "12px", color: "#555", textTransform: "uppercase", letterSpacing: "1px" }}>
                📋 {result.slides?.length || 0} Bagian Thread
              </span>
              <button onClick={handleCopyAll} style={{
                padding: "6px 14px", borderRadius: "6px", cursor: "pointer",
                border: "1px solid #2a2a2a",
                background: copiedAll ? "rgba(74,222,128,0.15)" : "#1a1a1a",
                color: copiedAll ? "#4ade80" : "#666",
                fontSize: "12px", fontFamily: "inherit", transition: "all 0.2s",
              }}>
                {copiedAll ? "✓ Semua Copied!" : "Copy Semua"}
              </button>
            </div>

            {/* Slides cards */}
            {result.slides?.map((slide, idx) => {
              const isAffiliate = idx === result.slides.length - 1;
              return (
                <div key={idx} style={{
                  background: isAffiliate ? "rgba(247,151,30,0.07)" : "#111",
                  border: `1px solid ${isAffiliate ? "rgba(247,151,30,0.25)" : "#222"}`,
                  borderRadius: "12px", overflow: "hidden", marginBottom: "10px",
                }}>
                  <div style={{
                    padding: "10px 14px", borderBottom: `1px solid ${isAffiliate ? "rgba(247,151,30,0.15)" : "#1a1a1a"}`,
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                  }}>
                    <span style={{ fontSize: "11px", color: isAffiliate ? "#f7971e" : "#444", fontWeight: 600 }}>
                      {isAffiliate ? "🛒 Affiliate CTA" : `Bagian ${idx + 1}`}
                    </span>
                    <button onClick={() => handleCopySlide(slide, idx)} style={{
                      padding: "4px 12px", borderRadius: "5px", cursor: "pointer",
                      border: "1px solid #2a2a2a",
                      background: copiedIdx === idx ? "rgba(74,222,128,0.15)" : "#1a1a1a",
                      color: copiedIdx === idx ? "#4ade80" : "#555",
                      fontSize: "11px", fontFamily: "inherit", transition: "all 0.2s",
                    }}>
                      {copiedIdx === idx ? "✓" : "Copy"}
                    </button>
                  </div>
                  <div style={{ padding: "14px", fontSize: "14px", color: isAffiliate ? "#e0c080" : "#ccc", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>
                    {slide}
                  </div>
                </div>
              );
            })}

            {/* Action Buttons */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginTop: "16px", marginBottom: "8px" }}>
              <button onClick={handleGenerate} disabled={loading} style={{
                padding: "12px", borderRadius: "8px", border: "1px solid #222",
                background: "#111", color: "#888", fontSize: "13px", cursor: "pointer",
                fontFamily: "inherit", fontWeight: 500,
              }}>
                🔄 Topik lain
              </button>
              <button onClick={() => { setResult(null); setAffiliateLink(""); }} style={{
                padding: "12px", borderRadius: "8px", border: "1px solid #222",
                background: "#111", color: "#888", fontSize: "13px", cursor: "pointer",
                fontFamily: "inherit", fontWeight: 500,
              }}>
                ✏️ Ganti link
              </button>
            </div>

            <p style={{ textAlign: "center", fontSize: "11px", color: "#333", marginTop: "12px", marginBottom: "32px" }}>
              Tip: copy tiap bagian → paste satu-satu di Threads sebagai reply ke diri sendiri
            </p>
          </div>
        )}

        {result?.error && (
          <div style={{ textAlign: "center", color: "#f87171", padding: "20px", fontSize: "14px" }}>
            ⚠️ Gagal generate, coba lagi ya!
          </div>
        )}
      </div>
    </div>
  );
}
