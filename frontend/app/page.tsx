const aaSections = [
  "AA 表格 A",
  "AA 表格 B",
  "AA 表格 C",
];

export default function HomePage() {
  return (
    <main className="container">
      <header className="toolbar">
        <h1>AI Dashboard</h1>
        <div className="actions">
          <select aria-label="来源筛选">
            <option>全部来源</option>
            <option>AA Tech</option>
            <option>AA Research</option>
            <option>AA Products</option>
            <option>HF Trending</option>
          </select>
          <button type="button">刷新</button>
        </div>
      </header>

      <section className="grid">
        {aaSections.map((title) => (
          <article key={title} className="card">
            <h2>{title}</h2>
            <p>预留 AA 数据表格区块。</p>
          </article>
        ))}
      </section>

      <section className="card">
        <h2>HF Trending</h2>
        <p>预留 Hugging Face 热门趋势区块。</p>
      </section>
    </main>
  );
}
