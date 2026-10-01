/** Small DOM helpers.
 *
 *  Every value that comes from massing.json is set through textContent, so no
 *  data is ever parsed as markup. Icons are real SVG nodes referencing the
 *  sprite in public/icons.svg, so there is no innerHTML anywhere in the viewer.
 */

const SVG_NS = 'http://www.w3.org/2000/svg';
const XLINK_NS = 'http://www.w3.org/1999/xlink';

export type Child = Node | string | null | undefined | false;

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Record<string, string> = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') el.className = v;
    else el.setAttribute(k, v);
  }
  append(el, children);
  return el;
}

export function append(el: Element, children: Child[]) {
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    el.append(typeof c === 'string' ? document.createTextNode(c) : c);
  }
}

/** An icon from the sprite in public/icons.svg. */
export function icon(name: string, cls = 'icon'): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('class', cls);
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS(SVG_NS, 'use');
  use.setAttribute('href', `icons.svg#${name}`);
  use.setAttributeNS(XLINK_NS, 'xlink:href', `icons.svg#${name}`);
  svg.append(use);
  return svg;
}

export function clear(el: Element) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

export function tr(label: string, value: string, valueClass = ''): HTMLTableRowElement {
  return h('tr', {},
    h('th', {}, label),
    h('td', valueClass ? { class: valueClass } : {}, value));
}

/** Text with one bolded fragment, built without markup parsing. */
export function textWithBold(before: string, bold: string, after = ''): DocumentFragment {
  const frag = document.createDocumentFragment();
  if (before) frag.append(document.createTextNode(before));
  frag.append(h('b', {}, bold));
  if (after) frag.append(document.createTextNode(after));
  return frag;
}
