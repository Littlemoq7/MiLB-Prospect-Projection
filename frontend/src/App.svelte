<script>
  const CATEGORIES = ['Below Average', 'Average', 'Above Average']

  let playerName = $state('')
  let status = $state('idle') // idle | loading | success | error
  let result = $state(null)
  let errorMessage = $state('')

  async function evaluatePlayer(event) {
    event.preventDefault()
    const name = playerName.trim()
    if (!name) return

    status = 'loading'
    errorMessage = ''

    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: name }),
      })
      const data = await response.json()

      if (!response.ok) {
        status = 'error'
        errorMessage = data.error || 'Something went wrong.'
        return
      }

      result = data
      status = 'success'
    } catch (err) {
      status = 'error'
      errorMessage = 'Could not reach the prediction service. Is the Flask server running?'
    }
  }
</script>

<main>
  <h1>Prospect Predictor</h1>
  <p class="subtitle">Predict a minor-league hitter's projected MLB performance tier.</p>

  <form onsubmit={evaluatePlayer}>
    <input
      type="text"
      placeholder="Player name, e.g. Roman Anthony"
      bind:value={playerName}
      disabled={status === 'loading'}
    />
    <button type="submit" disabled={status === 'loading' || !playerName.trim()}>
      {status === 'loading' ? 'Evaluating…' : 'Evaluate'}
    </button>
  </form>

  {#if status === 'error'}
    <p class="error">{errorMessage}</p>
  {/if}

  {#if status === 'success' && result}
    <section class="result-card">
      <h2>{result.name}</h2>
      <div class="category-badge category-{result.category.toLowerCase().replaceAll(' ', '-')}">
        {result.category}
        <span class="confidence">{Math.round(result.confidence * 100)}% confidence</span>
      </div>

      <div class="bars">
        {#each CATEGORIES as category}
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
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    background: #0f172a;
    color: #e2e8f0;
    font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  }

  main {
    max-width: 32rem;
    margin: 0 auto;
    padding: 3rem 1.5rem 4rem;
    text-align: center;
  }

  h1 {
    margin-bottom: 0.25rem;
    font-size: 2rem;
  }

  .subtitle {
    margin-top: 0;
    color: #94a3b8;
    font-size: 0.95rem;
  }

  form {
    display: flex;
    gap: 0.5rem;
    margin: 2rem 0;
  }

  input {
    flex: 1;
    padding: 0.65rem 0.9rem;
    border-radius: 0.5rem;
    border: 1px solid #334155;
    background: #1e293b;
    color: #e2e8f0;
    font-size: 1rem;
  }

  input:focus {
    outline: 2px solid #3b82f6;
    outline-offset: 1px;
  }

  button {
    padding: 0.65rem 1.2rem;
    border-radius: 0.5rem;
    border: none;
    background: #3b82f6;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  button:disabled {
    background: #334155;
    cursor: not-allowed;
  }

  .error {
    color: #f87171;
    font-weight: 500;
  }

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
