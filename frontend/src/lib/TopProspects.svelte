<script>
  let players = $state([])
  let status = $state('loading') // loading | success | error

  async function load() {
    try {
      const res = await fetch('/api/top-prospects')
      if (!res.ok) {
        status = 'error'
        return
      }
      players = await res.json()
      status = 'success'
    } catch (err) {
      status = 'error'
    }
  }
  load()
</script>

<section class="top-prospects">
  <h2>Top 2025 MiLB Prospects</h2>
  <p class="subtitle">Highest model confidence of an "Above Average" MLB career, among players with a 2025 minor-league season.</p>

  {#if status === 'loading'}
    <p class="status">Loading…</p>
  {:else if status === 'error'}
    <p class="status error">Could not load top prospects.</p>
  {:else if players.length === 0}
    <p class="status">No qualifying players found.</p>
  {:else}
    <ol>
      {#each players as player, i}
        <li>
          <span class="rank">{i + 1}</span>
          <span class="name">{player.name}</span>
          <span class="confidence">{Math.round(player.confidence * 100)}%</span>
        </li>
      {/each}
    </ol>
  {/if}
</section>

<style>
  .top-prospects {
    text-align: left;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-top: 2.5rem;
  }

  h2 {
    margin: 0 0 0.25rem;
    font-size: 1.15rem;
  }

  .subtitle {
    margin: 0 0 1.25rem;
    color: #94a3b8;
    font-size: 0.85rem;
  }

  .status {
    color: #94a3b8;
    font-size: 0.9rem;
  }

  .status.error {
    color: #f87171;
  }

  ol {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  li {
    display: grid;
    grid-template-columns: 1.75rem 1fr auto;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.6rem;
    background: #0f172a;
    border-radius: 0.5rem;
  }

  .rank {
    color: #64748b;
    font-weight: 700;
    font-size: 0.9rem;
  }

  .name {
    font-weight: 600;
  }

  .confidence {
    color: #4ade80;
    font-weight: 700;
    font-size: 0.9rem;
  }
</style>
