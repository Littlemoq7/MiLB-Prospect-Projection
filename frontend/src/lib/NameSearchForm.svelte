<script>
  let { busy = false, onSubmit } = $props()

  let name = $state('')
  let suggestions = $state([])
  let showSuggestions = $state(false)
  let activeIndex = $state(-1)

  let debounceTimer
  let controller

  function clearSuggestions() {
    suggestions = []
    showSuggestions = false
    activeIndex = -1
  }

  function fetchSuggestions(query) {
    clearTimeout(debounceTimer)
    if (!query) {
      clearSuggestions()
      return
    }
    debounceTimer = setTimeout(async () => {
      controller?.abort()
      controller = new AbortController()
      try {
        const res = await fetch(`/api/player-names?q=${encodeURIComponent(query)}`, {
          signal: controller.signal,
        })
        const names = res.ok ? await res.json() : []
        suggestions = names
        showSuggestions = names.length > 0
        activeIndex = -1
      } catch (err) {
        if (err.name !== 'AbortError') clearSuggestions()
      }
    }, 150)
  }

  function selectSuggestion(suggestion) {
    name = suggestion
    clearSuggestions()
  }

  function handleKeydown(event) {
    if (!showSuggestions || !suggestions.length) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      activeIndex = (activeIndex + 1) % suggestions.length
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      activeIndex = (activeIndex - 1 + suggestions.length) % suggestions.length
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault()
      selectSuggestion(suggestions[activeIndex])
    } else if (event.key === 'Escape') {
      clearSuggestions()
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    clearSuggestions()
    onSubmit(trimmed)
  }
</script>

<form onsubmit={handleSubmit}>
  <div class="autocomplete">
    <input
      type="text"
      placeholder="Player name, e.g. Roman Anthony"
      bind:value={name}
      oninput={() => fetchSuggestions(name.trim())}
      onkeydown={handleKeydown}
      onblur={() => setTimeout(clearSuggestions, 100)}
      disabled={busy}
      autocomplete="off"
    />
    {#if showSuggestions}
      <ul class="suggestions">
        {#each suggestions as suggestion, i}
          <li>
            <button
              type="button"
              class:active={i === activeIndex}
              onmousedown={(event) => {
                event.preventDefault()
                selectSuggestion(suggestion)
              }}
            >
              {suggestion}
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
  <button type="submit" disabled={busy || !name.trim()}>
    {busy ? 'Evaluating…' : 'Evaluate'}
  </button>
</form>

<style>
  form {
    display: flex;
    gap: 0.5rem;
    margin: 2rem 0;
    align-items: flex-start;
  }

  .autocomplete {
    position: relative;
    flex: 1;
  }

  input {
    width: 100%;
    box-sizing: border-box;
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

  .suggestions {
    position: absolute;
    top: calc(100% + 0.25rem);
    left: 0;
    right: 0;
    margin: 0;
    padding: 0.25rem;
    list-style: none;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    max-height: 14rem;
    overflow-y: auto;
    z-index: 10;
    text-align: left;
  }

  .suggestions li button {
    display: block;
    width: 100%;
    padding: 0.5rem 0.6rem;
    border: none;
    background: none;
    color: #e2e8f0;
    text-align: left;
    font-size: 0.95rem;
    border-radius: 0.35rem;
    cursor: pointer;
  }

  .suggestions li button:hover,
  .suggestions li button.active {
    background: #334155;
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
    white-space: nowrap;
  }

  button[type='submit']:disabled {
    background: #334155;
    cursor: not-allowed;
  }
</style>
