/* TruthAngel Linkify & Sources helper (standalone, no deps)
   Usage:
     1) <script src="/assets/js/ta-linkify.js"></script>
     2) In success handler:
          const enhanced = TALinkify.enhance(bodyHtml, data.sources || data.citations || data.refs || []);
          finish(enhanced);

   Tablet Mode:
     Set window.TABLET_CONFIG.sourcesClickable = false to disable external links
     Sources will display as text instead of clickable links
*/
(function (global) {
  'use strict';

  // Check if external links should be disabled (tablet mode)
  function shouldDisableLinks() {
    return window.TABLET_CONFIG && window.TABLET_CONFIG.disableExternalLinks === true;
  }

  // Check if sources should be clickable
  function shouldSourcesBeClickable() {
    if (!window.TABLET_CONFIG) return true;
    return window.TABLET_CONFIG.sourcesClickable !== false;
  }

  function normalizeUrl(u){
    if (!u) return "";
    u = String(u).trim().replace(/[)\]\.,;:]+$/, "");
    if (/^https?:\/\//i.test(u)) return u;
    if (/^www\./i.test(u)) return "https://" + u;
    return u;
  }

  function ensureStyles(){
    if (document.getElementById('ta-linkify-styles')) return;
    const style = document.createElement('style');
    style.id = 'ta-linkify-styles';
    style.textContent = [
      '.sources{margin:10px 0 0;padding:10px 12px;border:1px solid rgba(255,255,255,.12);',
      'border-radius:10px;background:rgba(255,255,255,.04);font-size:.95rem;}',
      '.sources b{color:#dfe9ff}',
      '.sources ul{margin:6px 0 0 18px;padding:0}',
      '.sources li{margin:4px 0}',
      '.sources a{text-decoration:underline}',
      // Tablet mode: non-clickable source styling
      '.source-text{color:#b6c3df;font-style:italic}',
      '.source-domain{color:#7aa7ff;font-weight:500}'
    ].join('');
    document.head.appendChild(style);
  }

  function linkifyHtmlSafe(html){
    const container = document.createElement('div');
    container.innerHTML = String(html);

    // In tablet mode with links disabled, don't linkify anything
    if (shouldDisableLinks()) {
      return container.innerHTML;
    }

    const urlRe = /(https?:\/\/[^\s<]+|www\.[^\s<]+)/g;
    const mdRe  = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;

    function process(node){
      if (node.nodeType === Node.TEXT_NODE) {
        let text = node.nodeValue;

        // Markdown first
        let frag = document.createDocumentFragment();
        let last = 0, m, any = false;
        mdRe.lastIndex = 0;
        while ((m = mdRe.exec(text))){
          any = true;
          frag.appendChild(document.createTextNode(text.slice(last, m.index)));
          const a = document.createElement('a');
          a.href = normalizeUrl(m[2]); a.target = "_blank"; a.rel = "noopener"; a.textContent = m[1];
          frag.appendChild(a);
          last = m.index + m[0].length;
        }
        if (any){
          frag.appendChild(document.createTextNode(text.slice(last)));
          node.replaceWith(frag);
          return;
        }

        // Bare URLs
        urlRe.lastIndex = 0; last = 0; any = false; frag = document.createDocumentFragment();
        while ((m = urlRe.exec(text))){
          any = true;
          frag.appendChild(document.createTextNode(text.slice(last, m.index)));
          const a = document.createElement('a');
          a.href = normalizeUrl(m[0]); a.target = "_blank"; a.rel = "noopener"; a.textContent = m[0];
          frag.appendChild(a);
          last = m.index + m[0].length;
        }
        if (any){
          frag.appendChild(document.createTextNode(text.slice(last)));
          node.replaceWith(frag);
        }
      } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName !== 'A' && node.tagName !== 'CODE') {
        Array.from(node.childNodes).forEach(process);
      }
    }

    Array.from(container.childNodes).forEach(process);
    return container.innerHTML;
  }

  // Extract domain from URL for display
  function extractDomain(url) {
    try {
      const u = new URL(normalizeUrl(url));
      return u.hostname.replace(/^www\./, '');
    } catch (e) {
      return url;
    }
  }

  function renderSources(sources){
    if (!Array.isArray(sources) || sources.length === 0) return "";

    const clickable = shouldSourcesBeClickable();

    const items = sources.map((s, i) => {
      if (typeof s === "string") {
        const match = s.match(/(https?:\/\/[^\s)]+|www\.[^\s)]+)/i);
        if (match) {
          const url = normalizeUrl(match[0]);
          const title = s.replace(match[0], "").trim() || url;

          if (clickable) {
            return '<li><a href="' + url + '" target="_blank" rel="noopener">' + title + '</a></li>';
          } else {
            // Tablet mode: show as text with domain
            const domain = extractDomain(url);
            return '<li><span class="source-text">' + title + '</span> <span class="source-domain">(' + domain + ')</span></li>';
          }
        }
        return '<li>' + s + '</li>';
      } else {
        const url   = normalizeUrl(s.url || s.href || s.link || s.source || "");
        const title = (s.title || s.name || s.label || s.domain || s.url || s.href || ('Source ' + (i+1)));

        if (clickable && url) {
          return '<li><a href="' + url + '" target="_blank" rel="noopener">' + title + '</a></li>';
        } else if (url) {
          // Tablet mode: show as text with domain
          const domain = extractDomain(url);
          return '<li><span class="source-text">' + title + '</span> <span class="source-domain">(' + domain + ')</span></li>';
        } else {
          return '<li>' + title + '</li>';
        }
      }
    }).join("");
    return '<div class="sources"><b>Sources</b><ul>' + items + '</ul></div>';
  }

  function enhance(bodyHtml, sourcesArray){
    ensureStyles();
    const linked = linkifyHtmlSafe(bodyHtml);
    const sources = renderSources(sourcesArray || []);
    return linked + sources;
  }

  global.TALinkify = { enhance, linkifyHtmlSafe, renderSources };
})(window);
