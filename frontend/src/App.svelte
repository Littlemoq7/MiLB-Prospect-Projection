<script>
  import NameSearchForm from './lib/NameSearchForm.svelte'
  import ManualStatsForm from './lib/ManualStatsForm.svelte'
  import ResultCard from './lib/ResultCard.svelte'

  let mode = $state('search') // search | manual
  let status = $state('idle') // idle | loading | success | error
  let result = $state(null)
  let errorMessage = $state('')

  function switchMode(next) {
    if (mode === next) return
    mode = next
    status = 'idle'
    result = null
    errorMessage = ''
  }

  async function runPrediction(makeRequest) {
    status = 'loading'
    errorMessage = ''
    try {
      const response = await makeRequest()
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

  function evaluateByName(name) {
    runPrediction(() =>
      fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: name }),
      })
    )
  }

  function evaluateManual(seasons) {
    runPrediction(() =>
      fetch('/api/predict-seasons', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seasons }),
      })
    )
  }
</script>

<main>
  <h1>Prospect Predictor</h1>
  <p class="subtitle">Predict a minor-league hitter's projected MLB performance tier.</p>

  <div class="tabs">
    <button type="button" class:active={mode === 'search'} onclick={() => switchMode('search')}>
      Search by name
    </button>
    <button type="button" class:active={mode === 'manual'} onclick={() => switchMode('manual')}>
      Enter stats manually
    </button>
  </div>

  {#if mode === 'search'}
    <NameSearchForm busy={status === 'loading'} onSubmit={evaluateByName} />
  {:else}
    <ManualStatsForm busy={status === 'loading'} onSubmit={evaluateManual} />
  {/if}

  {#if status === 'error'}
    <p class="error">{errorMessage}</p>
  {/if}

  {#if status === 'success' && result}
    <ResultCard {result} title={result.name ?? null} />
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

  .tabs {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
  }

  .tabs button {
    padding: 0.5rem 1rem;
    border-radius: 999px;
    border: 1px solid #334155;
    background: transparent;
    color: #94a3b8;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
  }

  .tabs button.active {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
  }

  .error {
    color: #f87171;
    font-weight: 500;
  }
</style>
