<script>
  let { result, title = null } = $props()
</script>

<section class="result-card">
  {#if title}
    <h2>{title}</h2>
  {/if}
  <div class="category-badge category-{result.category.toLowerCase().replaceAll(' ', '-')}">
    {result.category}
    <span class="confidence">{Math.round(result.confidence * 100)}% confidence</span>
  </div>

  <div class="bars">
    {#each Object.keys(result.probabilities) as category}
      {@const value = result.probabilities[category] ?? 0}
      <div class="bar-row">
        <span class="bar-label">{category}</span>
        <div class="bar-track">
          <div
            class="bar-fill"
            class:predicted={category === result.category}
            style:width="{Math.max(value * 100, 2)}%"
          ></div>
        </div>
        <span class="bar-value">{Math.round(value * 100)}%</span>
      </div>
    {/each}
  </div>
</section>

<style>
  .result-card {
    text-align: left;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-top: 1.5rem;
  }

  .result-card h2 {
    margin: 0 0 0.75rem;
    text-align: center;
  }

  .category-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.15rem;
    margin: 0 auto 1.5rem;
    padding: 0.5rem 1rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 1.1rem;
    width: fit-content;
  }

  .category-badge .confidence {
    font-weight: 400;
    font-size: 0.8rem;
    opacity: 0.85;
  }

  .category-did-not-reach-mlb {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
  }

  .category-below-average {
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
  }

  .category-average {
    background: rgba(250, 204, 21, 0.15);
    color: #facc15;
  }

  .category-above-average {
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
  }

  .bars {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .bar-row {
    display: grid;
    grid-template-columns: 7.5rem 1fr 3rem;
    align-items: center;
    gap: 0.6rem;
  }

  .bar-label {
    font-size: 0.85rem;
    color: #94a3b8;
  }

  .bar-track {
    background: #0f172a;
    border-radius: 999px;
    height: 0.6rem;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    background: #475569;
    border-radius: 999px;
    transition: width 0.4s ease;
  }

  .bar-fill.predicted {
    background: #3b82f6;
  }

  .bar-value {
    font-size: 0.85rem;
    color: #94a3b8;
    text-align: right;
  }
</style>
