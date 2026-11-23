<!--
  How Early Is Flu in the US This Year? Every flu season since 2007-08 inside one large virus particle. Each season is a ring,
  the oldest nearest the center and this season on the outside, and every ring carries one spike per
  week, starting in early October at the top and running clockwise. Spike length is the share of
  outpatient visits for influenza-like illness. A dot marks the week each season began.
  D3 handles the scales and the dates, and Svelte holds the rings, the selection and the panel.
-->
<script>
  import { curveCatmullRom, curveCatmullRomClosed, descending, lineRadial, pointer, scaleLinear, timeFormat, utcParse } from 'd3';
  import raw from './flu-onset/data.json';
  import { NW, ROSE, SEPIA, SLATE, angleOf } from './flu-onset/clock.js';
  import './flu-onset/rings.css';

  let { title = false } = $props();

  // 2007-08 is the first season whose national baseline CDC still publishes, so every ring
  // uses CDC's own baseline rather than an estimate.
  const START = 2007;
  const seasons = raw.seasons.filter((s) => s.season >= START);
  const N = seasons.length, NOW = raw.meta.currentWeek, CUR = seasons[N - 1].season;
  const cur = seasons[N - 1];
  const parse = utcParse('%Y-%m-%d'), day = timeFormat('%B %-d'), short = timeFormat('%b %-d'), dayY = timeFormat('%b %-d, %Y');
  const weekEnd = (s, w) => new Date(parse(s.start).getTime() + w * 7 * 864e5);
  const pct = (v) => `${v.toFixed(1)}%`;
  const hueOf = (s) => (s.season === CUR ? ROSE : s.season === 2009 ? SLATE : SEPIA);

  // Geometry. The envelope is the inner circle; each season gets a band outside it.
  // A ring is a plain circle until flu rises above that season's usual level, and then it swells
  // outward by how far above. So every bulge is a flu season, and nothing else moves the line.
  const RIN = 78, ROUT = 330, BAND = (ROUT - RIN) / N;
  const swell = scaleLinear([0, 6.5], [0, BAND * 3.2]).clamp(true);
  const rb = (i) => RIN + i * BAND;
  const f = (n) => Math.round(n * 10) / 10;
  const circle = (r) => `M${f(r)},0A${f(r)},${f(r)} 0 1 0 ${f(-r)},0A${f(r)},${f(r)} 0 1 0 ${f(r)},0`;

  // Every other ring is drawn half a week on, so the spikes of neighboring seasons interleave
  // instead of lining up into spokes. The dates in the panel are exact.
  const shift = (i) => (i % 2) * 0.5;
  const rings = seasons.map((s, i) => {
    const until = s.season === CUR ? NOW : NW - 1;
    const pts = [];
    for (let w = 0; w <= until; w++) if (s.weeks[w] != null) pts.push({ w, v: s.weeks[w] });
    const rOf = (p) => rb(i) + swell(Math.max(0, p.v - s.baseline)), aOf = (p) => ((p.w + shift(i)) / NW) * Math.PI * 2;
    const whole = s.season !== CUR;
    const wave = lineRadial().angle(aOf).radius(rOf).curve(whole ? curveCatmullRomClosed : curveCatmullRom)(pts);
    // The stretch above the usual level, with one week either side so the bulge is drawn whole.
    const hotIdx = new Set();
    pts.forEach((p, k) => { if (Math.round(p.v * 10) / 10 >= s.baseline) { hotIdx.add(k - 1); hotIdx.add(k); hotIdx.add(k + 1); } });
    const hot = lineRadial().angle(aOf).radius(rOf).curve(curveCatmullRom).defined((p, k) => hotIdx.has(k))(pts);
    const rest = s.season === CUR ? lineRadial().angle(aOf).radius(() => rb(i)).curve(curveCatmullRom)(Array.from({ length: NW - NOW }, (_, k) => ({ w: NOW + k }))) : '';
    // Every week is a data point. A week above the usual level is a spike from the ring out to
    // the swollen line, with a head like the spikes of the real virus. A usual week is a dot on the ring.
    let spikes = '', heads = '', dots = '';
    const hr = 1.05;
    for (const p of pts) {
      const a = angleOf(p.w + shift(i)), dx = Math.cos(a), dy = Math.sin(a), r0 = rb(i);
      if (Math.round(p.v * 10) / 10 >= s.baseline) {
        const L = rOf(p) + 1.2;
        spikes += `M${f(dx * r0)},${f(dy * r0)}L${f(dx * L)},${f(dy * L)}`;
        const cx = dx * (L + hr), cy = dy * (L + hr);
        heads += `M${f(cx + hr)},${f(cy)}A${hr},${hr} 0 1 0 ${f(cx - hr)},${f(cy)}A${hr},${hr} 0 1 0 ${f(cx + hr)},${f(cy)}`;
      } else {
        const cx = dx * r0, cy = dy * r0, d = 0.55;
        dots += `M${f(cx + d)},${f(cy)}A${d},${d} 0 1 0 ${f(cx - d)},${f(cy)}A${d},${d} 0 1 0 ${f(cx + d)},${f(cy)}`;
      }
    }
    return { s, i, wave, hot, rest, rOf, spikes, heads, dots };
  });

  // The week each season began, one dot per ring.
  const onsetPts = rings.filter((g) => g.s.onset != null).map((g) => {
    const a = angleOf(g.s.onset + shift(g.i)), r = rb(g.i);
    return { s: g.s, x: Math.cos(a) * r, y: Math.sin(a) * r, early: g.s.onset < cur.onset };
  });

  // Months around the outside, and year labels along the quiet late-summer side.
  const months = [];
  for (let w = 0; w < NW; w++) {
    const d = weekEnd(cur, w), prev = w ? weekEnd(cur, w - 1) : null;
    if (!prev || d.getUTCMonth() !== prev.getUTCMonth()) {
      const a = angleOf(w);
      months.push({ w, a, x: Math.cos(a) * (ROUT + 34), y: Math.sin(a) * (ROUT + 34), t: timeFormat('%b')(d) });
    }
  }
  const LABEL_W = 44.5; // between late July and early August, where no season has flu
  const la = angleOf(LABEL_W);
  const tick = (a, r1, r2) => `M${f(Math.cos(a) * r1)},${f(Math.sin(a) * r1)}L${f(Math.cos(a) * r2)},${f(Math.sin(a) * r2)}`;

  // How this season's start compares with the seasons before it in the picture.
  const past = seasons.filter((s) => s.season !== CUR);
  const earlier = past.filter((s) => s.onset != null && s.onset < cur.onset).length;
  const same = past.filter((s) => s.onset === cur.onset).length;
  const rankNow = [...seasons].sort((a, b) => descending(a.weeks[NOW] ?? -1, b.weeks[NOW] ?? -1)).findIndex((s) => s.season === CUR) + 1;
  const ordinal = ['', 'highest', 'second highest', 'third highest', 'fourth highest', 'fifth highest'];

  let pick = $state(CUR);
  let over = $state(null);
  let compare = $state(false);
  let svg;
  const lit = $derived(over ?? pick);
  const sel = $derived(seasons.find((s) => s.season === lit));
  const selRing = $derived(rings.find((g) => g.s.season === lit));

  function ringAt(e) {
    const [x, y] = pointer(e, svg), r = Math.hypot(x, y), i = Math.floor((r - RIN) / BAND);
    return i >= 0 && i < N ? seasons[i].season : null;
  }
  function onkey(e) {
    const i = seasons.findIndex((s) => s.season === pick);
    if (e.key === 'ArrowUp' || e.key === 'ArrowRight') { e.preventDefault(); pick = seasons[Math.min(N - 1, i + 1)].season; }
    if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') { e.preventDefault(); pick = seasons[Math.max(0, i - 1)].season; }
  }
  const earliest = [...past].filter((s) => s.onset != null).sort((a, b) => a.onset - b.onset || a.season - b.season)[0];
  const highest = [...past].sort((a, b) => descending(a.peak, b.peak))[0];
  const began = (s) => (s.onset == null ? 'no clear start' : `week ending ${dayY(weekEnd(s, s.onset))}${s.provisional ? ', provisional' : ''}`);
</script>

<div class="fr">
  <div class="stage">
    <!-- svelte-ignore a11y_no_noninteractive_tabindex, a11y_no_noninteractive_element_interactions -->
    <svg
      bind:this={svg}
      viewBox="{-ROUT - 70} {-ROUT - 70} {(ROUT + 70) * 2} {(ROUT + 70) * 2}"
      tabindex="0"
      role="application"
      aria-label="{N} US flu seasons from {seasons[0].label} to {cur.label} as rings of one virus particle. The chosen season is {sel.label}, which began in the {began(sel)}. Use the arrow keys to move between seasons."
      onpointermove={(e) => (over = ringAt(e))}
      onpointerleave={() => (over = null)}
      onclick={(e) => { const s = ringAt(e); if (s != null) pick = s; }}
      onkeydown={onkey}
    >
      {#each months as m (m.w)}
        <path class="mtick" d={tick(m.a, ROUT + 18, ROUT + 24)} />
        <text class="month" x={m.x} y={m.y + 4}>{m.t}</text>
      {/each}

      <g class="all" class:quiet={over != null || pick !== CUR}>
        {#each rings as g (g.s.season)}
          <path class="wave" d={g.wave} stroke={hueOf(g.s)} />
          <path class="dots" d={g.dots} fill={hueOf(g.s)} />
          <path class="spikes" d={g.spikes} stroke={hueOf(g.s)} />
          <path class="heads" d={g.heads} stroke={hueOf(g.s)} />
          {#if g.rest}<path class="rest" d={g.rest} stroke={hueOf(g.s)} />{/if}
        {/each}
      </g>

      <!-- The week this season began, across every ring. Dots before it began earlier. -->
      <path class="guide" d={tick(angleOf(cur.onset), RIN - 4, ROUT + 14)} />
      <path class="guide" d={tick(angleOf(cur.onset), ROUT + 14, ROUT + 46)} />
      <text class="glab" x={Math.cos(angleOf(cur.onset)) * (ROUT + 50) + 4} y={Math.sin(angleOf(cur.onset)) * (ROUT + 50)}>{cur.provisional ? 'this season crossed' : 'this season began'}</text>
      {#if compare}
        <path class="hand" d={tick(angleOf(NOW), RIN - 4, ROUT + 14)} />
        <text class="hlab" x={Math.cos(angleOf(NOW)) * (ROUT + 20)} y={Math.sin(angleOf(NOW)) * (ROUT + 20) + 10}>this week, {short(weekEnd(cur, NOW))}</text>
      {/if}

      {#if selRing}
        <g class="chosen">
          <path class="wave" d={selRing.wave} stroke={hueOf(selRing.s)} />
          <path class="dots" d={selRing.dots} fill={hueOf(selRing.s)} />
          <path class="spikes" d={selRing.spikes} stroke={hueOf(selRing.s)} />
          <path class="heads" d={selRing.heads} stroke={hueOf(selRing.s)} />
          {#if selRing.rest}<path class="rest" d={selRing.rest} stroke={hueOf(selRing.s)} />{/if}
        </g>
      {/if}

      {#each onsetPts as p (p.s.season)}
        <circle class="odot" class:on={p.s.season === lit} class:late={!p.early && p.s.season !== CUR} cx={p.x} cy={p.y} r={p.s.season === lit || p.s.season === CUR ? 3.4 : 2.3} fill={p.early || p.s.season === CUR ? hueOf(p.s) : '#fff'} stroke={hueOf(p.s)} />
      {/each}

      {#each rings as g (g.s.season)}
        {#if g.i % 2 === 0 || g.s.season === lit || g.s.season === CUR}
          <text class="ylab" class:on={g.s.season === lit} x={Math.cos(la) * (rb(g.i) + BAND / 2)} y={Math.sin(la) * (rb(g.i) + BAND / 2) + 3}>{String(g.s.season).slice(2)}</text>
        {/if}
      {/each}

      <path class="env" d={circle(RIN - 6)} />
      <text class="c1" y="-8" fill={hueOf(sel)}>{sel.label}</text>
      <text class="c2" y="10">{sel.onset == null ? 'no clear start' : `${sel.provisional ? 'crossed' : 'began'} ${short(weekEnd(sel, sel.onset))}`}</text>
      <text class="c2" y="24">{sel.season === CUR ? 'so far' : 'peak'} {pct(sel.peak)}</text>
    </svg>
  </div>

  <div class="side">
    {#if title}<h1 class="title">How Early Is Flu in the US This Year?</h1>{/if}
    <p class="lede">Flu season in the United States began early this year. This is every season since 2007 inside one particle of the virus, the oldest at the center and this one on the outside.</p>
    <p class="rule">Each ring is one flu season, running clockwise from early October at the top, like a clock. Every week is a point on its ring. A usual week is a small dot. When doctor visits for flu-like illness rise above CDC's baseline for that season, the week becomes a spike, and the higher they go, the longer the spike, so each flu season swells out of its ring.</p>
    <div class="how" aria-hidden="true">
      <svg viewBox="0 0 300 74">
        <path class="howbase" d="M6,52 L294,52" />
        <path class="howline" d="M70,52 C92,52 96,18 128,16 C160,14 176,50 214,52" />
        {#each [6, 22, 38, 54, 230, 246, 262, 278, 294] as x (x)}<circle class="howdot" cx={x} cy="52" r="1.3" />{/each}
        {#each [[70, 50], [86, 42], [102, 28], [118, 18], [134, 16], [150, 22], [166, 33], [182, 43], [198, 49]] as [x, y] (x)}
          <path class="howspike" d="M{x},52L{x},{y - 3}" /><circle class="howhead" cx={x} cy={y - 5} r="2" />
        {/each}
        <circle cx="70" cy="52" r="3.4" fill={SEPIA} stroke={SEPIA} />
        <text x="70" y="70">began</text>
        <text x="134" y="6">peak</text>
        <text x="262" y="44">usual weeks</text>
      </svg>
    </div>
    <ul class="key">
      <li><i style:border-color={ROSE}></i>This season, on the outside</li>
      <li><i style:border-color={SEPIA}></i>Earlier seasons, oldest at the center</li>
      <li><i style:border-color={SLATE}></i>2009–10, the H1N1 pandemic, which peaked in October</li>
      <li><b class="dot full"></b>Began earlier than this season</li>
      <li><b class="dot"></b>Began later</li>
    </ul>
    <p class="finding">
      This season rose above CDC's baseline in the week ending {day(weekEnd(cur, cur.onset))}{cur.provisional ? ' and has stayed above it since. A season counts as begun after three weeks above, so this start is confirmed if the next week stays above too' : ''}. Of the {past.length} seasons before it, {earlier} began earlier and {same} began the same week. By the week ending {day(weekEnd(cur, NOW))}, {pct(cur.weeks[NOW])} of visits were for flu-like illness, the {ordinal[rankNow] ?? `number ${rankNow}`} level of any season at that point.
    </p>

    <div class="pickrow">
      <label for="fr-season">Choose a winter</label>
      <select id="fr-season" bind:value={pick}>
        {#each [...seasons].reverse() as s (s.season)}<option value={s.season}>{s.label}</option>{/each}
      </select>
    </div>
    <div class="seg">
      <button type="button" aria-pressed={pick === CUR} onclick={() => (pick = CUR)}>This season</button>
      <button type="button" aria-pressed={pick === earliest.season} onclick={() => (pick = earliest.season)}>Earliest start</button>
      <button type="button" aria-pressed={pick === highest.season} onclick={() => (pick = highest.season)}>Highest peak</button>
    </div>

    <div class="facts" aria-live="polite">
      <h3 style:color={hueOf(sel)}>{sel.label}</h3>
      <div class="row"><span>Began</span><b>{began(sel)}</b></div>
      <div class="row"><span>{sel.season === CUR ? 'Highest so far' : 'Peak'}</span><b>{pct(sel.peak)}, {dayY(weekEnd(sel, sel.peakWeek))}</b></div>
      <div class="row"><span>Weeks above the baseline</span><b>{sel.above}{sel.season === CUR ? ' so far' : ''}</b></div>
      <div class="row"><span>CDC baseline</span><b>{pct(sel.baseline)} of visits</b></div>
      {#if sel.season !== CUR && sel.weeks[NOW] != null}
        <div class="row"><span>At this point in the season</span><b>{pct(sel.weeks[NOW])}, against {pct(cur.weeks[NOW])} now</b></div>
      {/if}
    </div>

    <label class="toggle"><input type="checkbox" bind:checked={compare} /> Mark this week of the season across every ring</label>
    <p class="src">Data: CDC ILINet, the weighted share of outpatient visits for influenza-like illness, nationally, through the week ending {day(parse(raw.meta.latest))}. The picture starts in 2007–08, the first season whose national baseline CDC still publishes. A season begins with the first of three weeks in a row at or above that baseline, the rule CDC's FluSight forecasts used. Every other ring is drawn half a week on so that the spikes of neighboring seasons do not line up, and the dates in the panel are exact.</p>
  </div>
</div>
