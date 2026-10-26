// Text extraction from uploaded files, entirely in the browser (nothing is uploaded).
// Libraries are imported on first use of each format.

const PDFJS = "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.3.289/build";
const JSZIP = "https://cdn.jsdelivr.net/npm/jszip@3.10.2/+esm";
export const MAX_BYTES = 25 * 1024 * 1024;

export const ACCEPT = ".txt,.md,.markdown,.text,.csv,.tsv,.html,.htm,.rtf,.pdf,.docx,.odt,.pptx,.xlsx";
const LEGACY = { doc: "Word 97-2003 (.doc)", xls: "Excel 97-2003 (.xls)", ppt: "PowerPoint 97-2003 (.ppt)" };

const xml = (s) => new DOMParser().parseFromString(s, "application/xml");
const byTag = (node, ns, name) => Array.from(node.getElementsByTagNameNS(ns, name));
const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const A = "http://schemas.openxmlformats.org/drawingml/2006/main";
const S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
const ODF = "urn:oasis:names:tc:opendocument:xmlns:text:1.0";

async function zip(file) {
  const { default: JSZip } = await import(JSZIP);
  return JSZip.loadAsync(await file.arrayBuffer());
}
const numbered = (names, re) =>
  names.filter((n) => re.test(n)).sort((a, b) => +a.match(/(\d+)\.xml$/)[1] - +b.match(/(\d+)\.xml$/)[1]);

async function docx(file) {
  const z = await zip(file);
  const doc = xml(await z.file("word/document.xml").async("string"));
  // Text boxes nest paragraphs inside paragraphs; give each run to its innermost paragraph only.
  const ownerP = (el) => {
    let n = el.parentNode;
    while (n && !(n.localName === "p" && n.namespaceURI === W)) n = n.parentNode;
    return n;
  };
  return byTag(doc, W, "p").map((p) => {
    let s = "";
    for (const el of p.getElementsByTagNameNS(W, "*")) {
      if (ownerP(el) !== p) continue;
      if (el.localName === "t") s += el.textContent;
      else if (el.localName === "tab") s += "\t";
      else if (el.localName === "br" || el.localName === "cr") s += "\n";
    }
    return s;
  }).join("\n\n");
}

async function pptx(file) {
  const z = await zip(file);
  const slides = numbered(Object.keys(z.files), /^ppt\/slides\/slide\d+\.xml$/);
  const out = [];
  for (const name of slides) {
    const doc = xml(await z.file(name).async("string"));
    for (const p of byTag(doc, A, "p")) out.push(byTag(p, A, "t").map((t) => t.textContent).join(""));
  }
  return out.join("\n\n");
}

async function odt(file) {
  const z = await zip(file);
  const doc = xml(await z.file("content.xml").async("string"));
  const blocks = [...byTag(doc, ODF, "h"), ...byTag(doc, ODF, "p")]
    .sort((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1));
  const text = (node) => {
    let s = "";
    for (const c of node.childNodes) {
      if (c.nodeType === Node.TEXT_NODE) s += c.textContent;
      else if (c.localName === "s") s += " ".repeat(+(c.getAttributeNS(ODF, "c") || 1));
      else if (c.localName === "tab") s += "\t";
      else if (c.localName === "line-break") s += "\n";
      else if (c.localName !== "note") s += text(c);
    }
    return s;
  };
  return blocks.map(text).join("\n\n");
}

async function xlsx(file) {
  const z = await zip(file);
  const sharedFile = z.file("xl/sharedStrings.xml");
  const shared = sharedFile
    ? byTag(xml(await sharedFile.async("string")), S, "si").map((si) => byTag(si, S, "t").map((t) => t.textContent).join(""))
    : [];
  const cells = [];
  for (const name of numbered(Object.keys(z.files), /^xl\/worksheets\/sheet\d+\.xml$/)) {
    const doc = xml(await z.file(name).async("string"));
    for (const c of byTag(doc, S, "c")) {
      const t = c.getAttribute("t");
      const v = byTag(c, S, "v")[0]?.textContent;
      if (t === "s" && v !== undefined) cells.push(shared[+v]);
      else if (t === "inlineStr") cells.push(byTag(c, S, "t").map((x) => x.textContent).join(""));
      else if (t === "str" && v) cells.push(v);
    }
  }
  return proseCells(cells);
}

// Spreadsheets mix labels, numbers and prose; keep cells that contain letters.
const proseCells = (cells) => cells.filter((c) => c && /\p{L}/u.test(c)).map((c) => c.trim()).join("\n\n");

function delimited(text, sep) {
  const cells = [];
  let cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') quoted = false;
      else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === sep || ch === "\n" || ch === "\r") { cells.push(cell); cell = ""; }
    else cell += ch;
  }
  cells.push(cell);
  return proseCells(cells);
}

function html(text) {
  const doc = new DOMParser().parseFromString(text, "text/html");
  doc.querySelectorAll("script,style,noscript,template,head").forEach((n) => n.remove());
  const BLOCK = /^(P|DIV|H[1-6]|LI|BLOCKQUOTE|PRE|TR|SECTION|ARTICLE|HEADER|FOOTER|ASIDE|DD|DT|FIGCAPTION|TD|TH)$/;
  let out = "";
  const walk = (node) => {
    for (const c of node.childNodes) {
      if (c.nodeType === Node.TEXT_NODE) out += c.textContent.replace(/\s+/g, " ");
      else if (c.nodeName === "BR") out += "\n";
      else if (c.nodeType === Node.ELEMENT_NODE) {
        const block = BLOCK.test(c.nodeName);
        if (block) out += "\n\n";
        walk(c);
        if (block) out += "\n\n";
      }
    }
  };
  walk(doc.body ?? doc);
  return out;
}

function rtf(text) {
  // Minimal RTF reader: paragraphs, escapes, \'hh (Windows-1252) and \uN characters.
  const cp1252 = new TextDecoder("windows-1252");
  let out = "", depth = 0, skipDepth = -1, ucSkip = 0;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === "{") { depth++; continue; }
    if (ch === "}") { if (depth === skipDepth) skipDepth = -1; depth--; continue; }
    if (ch === "\\") {
      const m = text.slice(i).match(/^\\([a-z]+)(-?\d+)? ?|^\\'([0-9a-f]{2})|^\\(.)/i);
      if (!m) continue;
      i += m[0].length - 1;
      if (skipDepth >= 0) continue;
      if (m[3]) out += cp1252.decode(new Uint8Array([parseInt(m[3], 16)]));
      else if (m[4] === "*" || /^(fonttbl|colortbl|stylesheet|info|pict|header|footer|footnote)$/.test(m[1] ?? "")) skipDepth = depth;
      else if (m[4]) out += m[4] === "~" ? " " : m[4] === "\n" || m[4] === "\r" ? "\n\n" : /[\\{}]/.test(m[4]) ? m[4] : "";
      else if (m[1] === "par" || m[1] === "line") out += m[1] === "par" ? "\n\n" : "\n";
      else if (m[1] === "tab") out += "\t";
      else if (m[1] === "u") { out += String.fromCharCode((+m[2] + 65536) % 65536); ucSkip = 1; }
      continue;
    }
    if (skipDepth >= 0 || ch === "\r" || ch === "\n") continue;
    if (ucSkip) { ucSkip--; continue; }
    out += ch;
  }
  return out;
}

async function pdf(file) {
  const pdfjs = await import(`${PDFJS}/pdf.min.mjs`);
  pdfjs.GlobalWorkerOptions.workerSrc = `${PDFJS}/pdf.worker.min.mjs`;
  const task = pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) });
  const doc = await task.promise;
  const pages = [];
  for (let n = 1; n <= doc.numPages; n++) {
    const { items } = await (await doc.getPage(n)).getTextContent();
    // Rebuild lines from text items, then start a new paragraph where the vertical gap
    // between lines is clearly larger than the normal line spacing.
    const lines = [];
    let line = null;
    for (const it of items) {
      const y = it.transform[5], h = Math.abs(it.transform[3]) || it.height || 10;
      if (!line || Math.abs(y - line.y) > h * 0.5) {
        line = { y, h, text: "" };
        lines.push(line);
      }
      line.text += it.str;
      if (it.hasEOL) line = null;
    }
    const gaps = lines.slice(1).map((l, i) => lines[i].y - l.y).filter((g) => g > 0).sort((a, b) => a - b);
    const normal = gaps.length ? gaps[gaps.length >> 1] : 12;
    let text = "";
    lines.forEach((l, i) => {
      if (!l.text.trim()) return;
      const gap = i ? lines[i - 1].y - l.y : 0;
      text += i && (gap > normal * 1.4 || gap < 0) ? "\n\n" : i ? "\n" : "";
      text += l.text.trim();
    });
    pages.push(text);
  }
  await task.destroy();
  return pages.join("\n\n").replace(/(\p{L})-\n(\p{Ll})/gu, "$1$2");
}

/** Returns { text, kind } or throws an Error with a user-facing message. */
export async function extractText(file) {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  if (LEGACY[ext]) throw new Error(`${LEGACY[ext]} files aren't supported. Save it as .${ext}x and try again.`);
  if (file.size > MAX_BYTES) throw new Error(`File is larger than ${MAX_BYTES / 1024 / 1024} MB.`);
  const asText = () => file.text();
  let text;
  switch (ext) {
    case "pdf": text = await pdf(file); break;
    case "docx": text = await docx(file); break;
    case "odt": text = await odt(file); break;
    case "pptx": text = await pptx(file); break;
    case "xlsx": text = await xlsx(file); break;
    case "csv": text = delimited(await asText(), ","); break;
    case "tsv": text = delimited(await asText(), "\t"); break;
    case "html": case "htm": text = html(await asText()); break;
    case "rtf": text = rtf(await asText()); break;
    case "txt": case "md": case "markdown": case "text": case "": text = await asText(); break;
    default: throw new Error(`.${ext} files aren't supported. Try PDF, Word, OpenDocument, PowerPoint, Excel, CSV, HTML, RTF or plain text.`);
  }
  text = text.replace(/\r\n?/g, "\n").replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
  if (!text) throw new Error(ext === "pdf"
    ? "No text found. This PDF may be a scanned image; text recognition (OCR) isn't supported."
    : "No text found in this file.");
  return { text, kind: ext.toUpperCase() };
}
