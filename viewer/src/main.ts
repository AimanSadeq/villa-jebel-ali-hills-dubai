/** Villa 5130272, Phase 1 massing viewer.
 *
 *  Shows the three massing options with real sun positions and cast shadows.
 *  All geometry and all solar data come from viewer/public/data/massing.json,
 *  which src/model/export_massing.py writes from the same code that produced
 *  the reports, so the browser and the PDFs cannot disagree.
 *
 *  CONCEPT DESIGN, NOT FOR CONSTRUCTION.
 */

import './style.css';
import { MassingScene } from './scene';
import { append, clear, h, icon, textWithBold, tr } from './dom';
import type { MassingData, MassingOption } from './types';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const PRESETS: { label: string; month: number; hour: number }[] = [
  { label: 'Aug 16:00, peak', month: 8, hour: 16 },
  { label: 'Jun noon', month: 6, hour: 12 },
  { label: 'Jun 18:00', month: 6, hour: 18 },
  { label: 'Dec noon', month: 12, hour: 12 },
];

const pct = (v: number) => `${Math.round(v * 100)}%`;

function section(iconName: string, title: string, ...body: (Node | string)[]) {
  const sec = h('section', {},
    h('h2', {}, icon(iconName), h('span', {}, title)));
  append(sec, body);
  return sec;
}

async function boot() {
  const res = await fetch('data/massing.json');
  if (!res.ok) throw new Error(`Cannot load data/massing.json (HTTP ${res.status})`);
  const data: MassingData = await res.json();

  const app = document.getElementById('app')!;
  clear(app);

  const stage = h('div', { id: 'stage' });
  const panel = h('aside', { id: 'panel' });
  const stamp = h('div', { id: 'stamp' }, data.meta.stamp);
  const hint = h('div', { id: 'hint' },
    'Drag to orbit, scroll to zoom, right-drag to pan');
  app.append(stage, panel, stamp, hint);

  const scene = new MassingScene(stage);
  scene.build(data);
  scene.start();

  let current: MassingOption =
    data.options.find((o) => o.key === data.recommended) ?? data.options[0];
  let month = 8;    // August, peak cooling season
  let hour = 16;

  // Header
  panel.append(h('header', {},
    h('h1', {}, `Villa ${data.meta.plot}`),
    h('p', { class: 'sub' }, data.meta.community),
    h('p', { class: 'phase' }, `Phase ${data.meta.phase} · Massing options`)));

  // Options
  const optButtons = new Map<string, HTMLButtonElement>();
  const optList = h('div', { class: 'opts' });
  const summary = h('p', { class: 'summary' });
  for (const o of data.options) {
    const btn = h('button', { class: 'opt', type: 'button' },
      h('strong', {}, o.key),
      h('span', {}, o.name));
    if (o.key === data.recommended) {
      btn.append(h('em', {}, icon('check', 'icon tiny'), 'Recommended'));
    }
    btn.addEventListener('click', () => {
      current = o;
      scene.showOption(o);
      render();
    });
    optButtons.set(o.key, btn);
    optList.append(btn);
  }
  panel.append(section('layers', 'Option', optList, summary));

  // Sun controls
  const monthLabel = h('span', {});
  const hourLabel = h('span', {});
  const monthInput = h('input', {
    id: 'month', type: 'range', min: '1', max: '12', step: '1', value: String(month),
  }) as HTMLInputElement;
  const hourInput = h('input', {
    id: 'hour', type: 'range',
    min: String(data.sun.hours[0]),
    max: String(data.sun.hours[data.sun.hours.length - 1]),
    step: '1', value: String(hour),
  }) as HTMLInputElement;
  const sunReadout = h('p', { class: 'readout' });

  monthInput.addEventListener('input', () => { month = +monthInput.value; render(); });
  hourInput.addEventListener('input', () => { hour = +hourInput.value; render(); });

  const chips = h('div', { class: 'chips' });
  for (const p of PRESETS) {
    const chip = h('button', { class: 'chip', type: 'button' }, p.label);
    chip.addEventListener('click', () => {
      month = p.month; hour = p.hour;
      monthInput.value = String(month);
      hourInput.value = String(hour);
      render();
    });
    chips.append(chip);
  }

  panel.append(section('sun', 'Sun',
    h('div', { class: 'row' },
      h('label', { for: 'month' }, icon('calendar'), monthLabel), monthInput),
    h('div', { class: 'row' },
      h('label', { for: 'hour' }, icon('sun'), hourLabel), hourInput),
    sunReadout, chips));

  // View. Plot-up rather than north-up, so the entrance and backyard sides read
  // as front and back instead of corners of a diamond.
  const views: { key: 'entrance' | 'aerial' | 'plan'; label: string }[] = [
    { key: 'entrance', label: 'Entrance side' },
    { key: 'aerial', label: 'Backyard side' },
    { key: 'plan', label: 'Plan, plot up' },
  ];
  const viewButtons = new Map<string, HTMLButtonElement>();
  const viewRow = h('div', { class: 'chips' });
  let activeView: string = 'aerial';
  for (const v of views) {
    const b = h('button', { class: 'chip', type: 'button' }, v.label);
    b.addEventListener('click', () => {
      activeView = v.key;
      scene.setView(v.key);
      for (const [k, btn] of viewButtons) btn.classList.toggle('on', k === activeView);
    });
    viewButtons.set(v.key, b);
    viewRow.append(b);
  }
  viewButtons.get('aerial')!.classList.add('on');

  const labelBox = h('input', { type: 'checkbox', checked: 'checked' }) as HTMLInputElement;
  labelBox.addEventListener('change', () => scene.setLabelsVisible(labelBox.checked));

  panel.append(section('ruler', 'View', viewRow,
    h('label', { class: 'inline-toggle' }, labelBox, 'Side numbers'),
    h('p', { class: 'note' },
      'Views are squared to the plot, not to north. Side 1 fronts the road and '
      + 'carries the entrance. Side 3 fronts landscape plot 5130274 and is the '
      + 'backyard in the recommended option.')));

  // Wall to boundary
  const setbackTable = h('table', { class: 'facades' });
  panel.append(section('ruler', 'Wall to boundary', setbackTable,
    h('p', { class: 'note' },
      `Shortest distance from the villa wall to each plot boundary. `
      + `The DDA minimum is ${data.site.setbackM} m on all sides.`)));

  // Metrics
  const metrics = h('table', { class: 'metrics' });
  panel.append(section('check', 'Shade on the pool', metrics));

  // Facades
  const facadeTable = h('table', { class: 'facades' },
    h('tr', {},
      h('th', {}, 'Side'), h('th', {}, 'Faces'),
      h('th', {}, 'Sum am'), h('th', {}, 'Sum pm'), h('th', {}, 'Adjacency')));
  for (const f of data.facades) {
    facadeTable.append(h('tr', {},
      h('td', {}, String(f.side)),
      h('td', {}, f.compass),
      h('td', {}, String(f.summerAm)),
      h('td', { class: f.summerPm >= 140 ? 'hot' : 'cool' }, String(f.summerPm)),
      h('td', { class: 'adj' }, f.adjacency)));
  }
  const northNote = h('p', { class: 'note' });
  if (data.site.trueNorthVerified) {
    northNote.append('kWh/m2 on the wall. True north verified against the DDA GIS.');
  } else {
    northNote.append(icon('warn', 'icon tiny'),
      'kWh/m2 on the wall. North is NOT yet verified.');
  }
  panel.append(section('compass', 'Facades', facadeTable, northNote));

  // Toggles
  const envBox = h('input', { type: 'checkbox', checked: 'checked' }) as HTMLInputElement;
  const wallBox = h('input', { type: 'checkbox', checked: 'checked' }) as HTMLInputElement;
  envBox.addEventListener('change', () => scene.setEnvelopeVisible(envBox.checked));
  wallBox.addEventListener('change', () => scene.setWallsVisible(wallBox.checked));
  panel.append(h('section', { class: 'toggles' },
    h('label', {}, envBox, `${data.site.setbackM} m setback line`),
    h('label', {}, wallBox, 'Boundary walls')));

  // Recommendation
  const rec = data.options.find((o) => o.key === data.recommended)!;
  panel.append(h('footer', {},
    h('h3', {}, icon('check'), 'Recommendation'),
    h('p', {}, textWithBold('', `Option ${rec.key}, ${rec.name}. `,
      `${pct(rec.metrics.coolingPmShade)} of the pool deck shaded through cooling ` +
      `season afternoons, complete from 17:00, while still giving ` +
      `${pct(rec.metrics.winterMiddaySun)} sun on the water at winter midday. ` +
      `The only option that wins on both.`)),
    h('p', { class: 'small' }, 'Awaiting owner decision. No option is approved.')));

  function sunAt(m: number, hr: number) {
    const row = data.sun.table.find((r) => r.month === m)!;
    const i = data.sun.hours.indexOf(hr);
    return { altitude: row.altitude[i], azimuth: row.azimuth[i] };
  }

  function render() {
    const { altitude, azimuth } = sunAt(month, hour);
    scene.setSun(altitude, azimuth);

    monthLabel.textContent = `21 ${MONTHS[month - 1]}`;
    hourLabel.textContent = `${String(hour).padStart(2, '0')}:00`;

    clear(sunReadout);
    if (altitude > 0) {
      sunReadout.append(
        textWithBold('Altitude ', `${altitude.toFixed(1)}°`, '  ·  azimuth '),
        h('b', {}, `${azimuth.toFixed(1)}°`));
    } else {
      sunReadout.append('Sun below the horizon');
    }

    for (const [key, btn] of optButtons) btn.classList.toggle('on', key === current.key);
    summary.textContent = current.summary;

    const m = current.metrics;
    clear(metrics);
    metrics.append(
      tr('Cooling season afternoons, mean', pct(m.coolingPmShade),
        m.coolingPmShade > 0.5 ? 'good' : 'bad'),
      tr('Worst hour tested', pct(m.coolingPmShadeMin)),
      tr('Winter midday sun on water', pct(m.winterMiddaySun)),
      tr('Ground floor', `${m.groundM2} m2`),
      tr('First floor', `${m.firstM2} m2`),
      tr('Open ground', `${m.openGroundM2} m2`),
      tr('Pool faces', `side ${m.poolNearestSide}, ${m.poolFaces}`, 'adj'));

    clear(setbackTable);
    setbackTable.append(h('tr', {},
      h('th', {}, 'Side'), h('th', {}, 'Faces'),
      h('th', {}, 'To wall'), h('th', {}, '')));
    for (const w of current.wallToBoundary) {
      const role = w.isMainAccess ? 'Entrance'
        : w.side === m.poolNearestSide ? 'Backyard' : 'Neighbour';
      setbackTable.append(h('tr', {},
        h('td', {}, String(w.side)),
        h('td', { class: 'adj' }, role),
        h('td', { class: w.meetsSetback ? 'cool' : 'hot' },
          `${w.distanceM.toFixed(2)} m`),
        h('td', { class: 'adj' }, w.meetsSetback ? 'ok' : 'under')));
    }

    const sparkCell = h('td', {});
    for (const hr of Object.keys(m.byHour).map(Number).sort((a, b) => a - b)) {
      const v = m.byHour[String(hr)];
      const bar = h('span', { class: 'bar', title: `${hr}:00  ${pct(v)}` });
      const fill = h('i', {});
      fill.style.height = `${Math.max(v * 100, 2)}%`;
      bar.append(fill, h('u', {}, String(hr)));
      sparkCell.append(bar);
    }
    metrics.append(h('tr', { class: 'spark' }, h('th', {}, 'By hour'), sparkCell));
  }

  render();
}

boot().catch((err) => {
  const app = document.getElementById('app')!;
  clear(app);
  app.append(h('div', { class: 'fatal' },
    h('h1', {}, 'Could not start the viewer'),
    h('pre', {}, String(err)),
    h('p', {}, 'Run '),
    h('code', {}, 'python src/model/export_massing.py'),
    h('p', {}, ' from the repository root, then reload.')));
  console.error(err);
});
