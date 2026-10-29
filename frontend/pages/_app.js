// Plain-English description: Root application component wrapping all pages with standard layout and basic styling.

export default function App({ Component, pageProps }) {
  return (
    <div style={{ maxWidth: "700px", margin: "40px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <header style={{ borderBottom: "1px solid #ccc", paddingBottom: "10px", marginBottom: "20px" }}>
        <h2>VibeCheck: Multimodal Virality Engine</h2>
      </header>
      <main>
        <Component {...pageProps} />
      </main>
    </div>
  );
}

