<script>
  let { busy = false, onSubmit } = $props()

  let fields = $state([])
  let levels = $state([])
  let seasons = $state([])

  function emptySeason() {
    const row = {}
    for (const field of fields) {
      row[field.name] = field.name === 'Level' ? (levels[0] ?? '') : ''
    }
    return row
  }

  // Seeds the first season row once the field/level metadata has loaded.
  $effect(() => {
    if (fields.length > 0 && seasons.length === 0) {
      seasons = [emptySeason()]
    }
  })

  async function loadFields() {
    const res = await fetch('/api/season-fields')
    const data = await res.json()
    fields = data.fields ?? []
    levels = data.levels ?? []
  }
  loadFields()

  function addSeason() {
    seasons = [...seasons, emptySeason()]
  }

  function removeSeason(index) {
    seasons = seasons.filter((_, i) => i !== index)
  }

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit(seasons.map((season) => ({ ...season })))
  }
</script>

<form onsubmit={handleSubmit} class="manual-form">
  {#each seasons as season, index (index)}
    <div class="season">
      <div class="season-header">
        <span>Season {index + 1}</span>
        {#if seasons.length > 1}
          <button type="button" class="remove" disabled={busy} onclick={() => removeSeason(index)}>
            Remove
          </button>
        {/if}
      </div>
      <div class="season-fields">
        {#each fields as field (field.name)}
          <label>
            <span class="field-name">{field.name}</span>
            <span class="hint">{field.hint}</span>
            {#if field.name === 'Level'}
              <select required disabled={busy} bind:value={season[field.name]}>
                {#each levels as level}
                  <option value={level}>{level}</option>
                {/each}
              </select>
            {:else if field.name === 'Season'}
              <input type="number" step="1" required disabled={busy} bind:value={season[field.name]} />
            {:else}
              <input type="number" step="any" required disabled={busy} bind:value={season[field.name]} />
            {/if}
          </label>
        {/each}
      </div>
    </div>
  {/each}

  <button type="button" class="add-season" disabled={busy || fields.length === 0} onclick={addSeason}>
    + Add another season
  </button>

  <button type="submit" disabled={busy || seasons.length === 0}>
    {busy ? 'Evaluating…' : 'Evaluate'}
  </button>
</form>

<style>
  .manual-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 2rem 0;
    text-align: left;
  }

  .season {
    border: 1px solid #334155;
    border-radius: 0.75rem;
    padding: 1rem;
    background: #1e293b;
  }

  .season-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    font-weight: 600;
  }

  .remove {
    padding: 0.2rem 0.5rem;
    border: none;
    border-radius: 0.35rem;
    background: none;
    color: #f87171;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .remove:disabled {
    color: #64748b;
    cursor: not-allowed;
  }

  .season-fields {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .field-name {
    font-weight: 600;
    font-size: 0.9rem;
  }

  .hint {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 400;
  }

  input,
  select {
    box-sizing: border-box;
    padding: 0.5rem 0.7rem;
    border-radius: 0.5rem;
    border: 1px solid #334155;
    background: #0f172a;
    color: #e2e8f0;
    font-size: 0.95rem;
  }

  input:focus,
  select:focus {
    outline: 2px solid #3b82f6;
    outline-offset: 1px;
  }

  .add-season {
    align-self: flex-start;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    border: 1px dashed #334155;
    background: transparent;
    color: #94a3b8;
    font-size: 0.9rem;
    cursor: pointer;
  }

  .add-season:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  button[type='submit'] {
    padding: 0.65rem 1.2rem;
    border-radius: 0.5rem;
    border: none;
    background: #3b82f6;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    align-self: flex-start;
  }

  button[type='submit']:disabled {
    background: #334155;
    cursor: not-allowed;
  }
</style>
