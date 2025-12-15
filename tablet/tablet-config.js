/**
 * TruthAngel Tablet Configuration System
 *
 * This file defines configuration profiles for different tablet deployment modes.
 * The main codebase (unlimited/index.html, ask/ask.html) reads these settings
 * to customize behavior without maintaining separate codebases.
 */

const TABLET_CONFIGS = {
    // Standard web experience (no restrictions)
    standard: {
        mode: 'standard',
        disableExternalLinks: false,
        largeText: false,
        simplifiedNav: false,
        fontSize: 1.0,  // multiplier
        showSources: true,
        sourcesClickable: true,
        allowedDomains: null,  // null = allow all
        customAPI: null,
        headerText: 'TruthAngel Unlimited',
        headerSubtext: 'Explore the complete taxonomy of human knowledge'
    },

    // Senior-friendly tablet mode
    senior: {
        mode: 'senior',
        disableExternalLinks: true,
        largeText: true,
        simplifiedNav: true,
        fontSize: 1.1,  // 10% larger text (was 30%, too big)
        showSources: true,
        sourcesClickable: false,  // Show sources but not as links
        allowedDomains: ['truthangel.org'],
        customAPI: null,
        headerText: 'TruthAngel',
        headerSubtext: 'Ask me anything'
    },

    // Consumer tablet mode (standard size, locked down)
    consumer: {
        mode: 'consumer',
        disableExternalLinks: true,
        largeText: false,
        simplifiedNav: false,
        fontSize: 1.0,
        showSources: true,
        sourcesClickable: false,
        allowedDomains: ['truthangel.org'],
        customAPI: null,
        headerText: 'TruthAngel',
        headerSubtext: 'Safe, unlimited knowledge exploration'
    },

    // Education tablet mode (future)
    education: {
        mode: 'education',
        disableExternalLinks: true,
        largeText: false,
        simplifiedNav: false,
        fontSize: 1.0,
        showSources: true,
        sourcesClickable: false,
        allowedDomains: ['truthangel.org'],  // Can expand to whitelist educational sites
        customAPI: null,
        headerText: 'TruthAngel for Education',
        headerSubtext: 'Safe research for students'
    },

    // Corporate tablet mode (future)
    corporate: {
        mode: 'corporate',
        disableExternalLinks: true,
        largeText: false,
        simplifiedNav: false,
        fontSize: 1.0,
        showSources: true,
        sourcesClickable: false,
        allowedDomains: null,  // Configured per deployment
        customAPI: null,  // Configured per deployment to company's AI
        headerText: 'Knowledge Portal',
        headerSubtext: 'Your company knowledge base'
    }
};

/**
 * Get the current tablet configuration
 * Reads from window.TABLET_MODE, sessionStorage, or URL parameter
 */
function getTabletConfig() {
    // Priority: 1) window.TABLET_MODE, 2) sessionStorage, 3) URL param, 4) 'standard'
    let mode = window.TABLET_MODE;

    if (!mode) {
        // Check sessionStorage
        try {
            mode = sessionStorage.getItem('TABLET_MODE');
        } catch (e) {}
    }

    if (!mode) {
        // Check URL parameter
        try {
            const params = new URLSearchParams(window.location.search);
            mode = params.get('tablet');
        } catch (e) {}
    }

    mode = mode || 'standard';

    // Store in sessionStorage for persistence across page navigations
    if (mode !== 'standard') {
        try {
            sessionStorage.setItem('TABLET_MODE', mode);
        } catch (e) {}
    }

    // Also set on window for other scripts
    window.TABLET_MODE = mode;

    return TABLET_CONFIGS[mode] || TABLET_CONFIGS.standard;
}

/**
 * Apply tablet configuration to the page
 * Call this on page load after DOM is ready
 */
function applyTabletConfig() {
    const config = getTabletConfig();

    // Apply font size multiplier
    if (config.fontSize !== 1.0) {
        document.documentElement.style.fontSize = `${config.fontSize * 100}%`;
    }

    // Add mode class to body for CSS targeting
    document.body.classList.add(`tablet-mode-${config.mode}`);

    // Store config globally for other scripts to access
    window.TABLET_CONFIG = config;

    return config;
}

/**
 * Check if external links should be disabled
 */
function shouldDisableExternalLinks() {
    const config = window.TABLET_CONFIG || getTabletConfig();
    return config.disableExternalLinks;
}

/**
 * Check if sources should be clickable
 */
function shouldSourcesBeClickable() {
    const config = window.TABLET_CONFIG || getTabletConfig();
    return config.sourcesClickable;
}

/**
 * Process a URL - returns null if it should be blocked, or the URL if allowed
 */
function processUrl(url) {
    const config = window.TABLET_CONFIG || getTabletConfig();

    // If no domain restrictions, allow all
    if (!config.allowedDomains) {
        return url;
    }

    try {
        const urlObj = new URL(url, window.location.origin);
        const hostname = urlObj.hostname.toLowerCase();

        // Check if domain is in allowed list
        for (const allowed of config.allowedDomains) {
            if (hostname === allowed || hostname.endsWith('.' + allowed)) {
                return url;
            }
        }

        // Domain not allowed
        return null;
    } catch (e) {
        // Invalid URL, block it
        return null;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TABLET_CONFIGS, getTabletConfig, applyTabletConfig, shouldDisableExternalLinks, shouldSourcesBeClickable, processUrl };
}
