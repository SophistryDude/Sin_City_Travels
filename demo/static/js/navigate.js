const Navigate = {
    currentNav: null,

    async startNavigation() {
        const startId = document.getElementById('route-start').value;
        const endId = document.getElementById('route-end').value;

        if (!startId || !endId) return;
        if (startId === endId) return;

        const resultDiv = document.getElementById('nav-result');
        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = '<div class="nav-loading">Calculating navigation...</div>';

        try {
            const navData = await API.navigate(startId, endId);
            this.currentNav = navData;
            SinCityMap.showMultiLegRoute(navData);
            this.renderResult(navData);
        } catch (err) {
            resultDiv.innerHTML = `<div class="nav-error">Error: ${err.message}</div>`;
        }
    },

    renderResult(nav) {
        const div = document.getElementById('nav-result');
        let html = this.renderSummary(nav);
        html += '<div id="nav-legs">';
        nav.legs.forEach(leg => {
            html += this.renderLeg(leg);
        });
        html += '</div>';
        div.innerHTML = html;

        // Wire up collapsible leg headers
        div.querySelectorAll('.leg-header').forEach(header => {
            header.addEventListener('click', () => {
                const card = header.parentElement;
                card.classList.toggle('collapsed');
            });
        });
    },

    renderSummary(nav) {
        const totalMin = Math.floor(nav.total_time_seconds / 60);
        const totalSec = nav.total_time_seconds % 60;
        const distDisplay = nav.total_distance_meters >= 1000
            ? (nav.total_distance_meters / 1000).toFixed(1) + ' km'
            : Math.round(nav.total_distance_meters) + ' m';

        const modeIcon = nav.mode === 'rideshare' ? '&#128663;' : '&#128694;';
        const modeLabel = nav.mode === 'rideshare' ? 'Rideshare' : 'Walking';

        return `
            <div class="nav-summary">
                <div class="nav-summary-header">
                    <span class="nav-from">${nav.start.name}</span>
                    <span class="nav-arrow">&#8594;</span>
                    <span class="nav-to">${nav.end.name}</span>
                </div>
                <div class="nav-stats">
                    <div class="nav-stat">
                        <div class="value">${totalMin}:${String(totalSec).padStart(2, '0')}</div>
                        <div class="label">Total Time</div>
                    </div>
                    <div class="nav-stat">
                        <div class="value">${distDisplay}</div>
                        <div class="label">Distance</div>
                    </div>
                    <div class="nav-stat">
                        <div class="value">${modeIcon} ${modeLabel}</div>
                        <div class="label">${nav.leg_count} ${nav.leg_count === 1 ? 'Leg' : 'Legs'}</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderLeg(leg) {
        const typeClass = leg.leg_type.replace('_', '-');
        const min = Math.floor(leg.estimated_time_seconds / 60);
        const sec = leg.estimated_time_seconds % 60;
        const timeStr = min > 0 ? `${min}m ${sec}s` : `${sec}s`;
        const distStr = Math.round(leg.distance_meters) + 'm';

        let bodyHtml = '';

        if (leg.leg_type === 'rideshare') {
            bodyHtml = this.renderRideshareCard(leg);
        }

        // Steps
        if (leg.steps && leg.steps.length > 0) {
            bodyHtml += '<div class="leg-steps">';
            leg.steps.forEach((step, i) => {
                const icon = this.stepIcon(step, leg, i);
                const stepDist = step.distance_meters > 0
                    ? `<span class="step-dist">${Math.round(step.distance_meters)}m</span>`
                    : '';
                bodyHtml += `
                    <div class="leg-step">
                        <span class="step-icon">${icon}</span>
                        <span class="step-text">${step.instruction}</span>
                        ${stepDist}
                    </div>
                `;
            });
            bodyHtml += '</div>';
        }

        return `
            <div class="leg-card ${typeClass}">
                <div class="leg-header">
                    <div class="leg-header-left">
                        <span class="leg-number">${leg.leg_number}</span>
                        <span class="leg-label">${leg.label}</span>
                    </div>
                    <div class="leg-header-right">
                        <span class="leg-time">${timeStr}</span>
                        <span class="leg-dist">${distStr}</span>
                        <span class="leg-toggle">&#9660;</span>
                    </div>
                </div>
                <div class="leg-body">
                    ${bodyHtml}
                </div>
            </div>
        `;
    },

    renderRideshareCard(leg) {
        const fare = leg.fare_estimates;
        const links = leg.deep_links;

        return `
            <div class="rideshare-card">
                <div class="rideshare-options">
                    <a href="${links.uber}" target="_blank" class="rideshare-btn uber-btn">
                        <span class="rs-name">Uber</span>
                        <span class="rs-fare">$${fare.uber.estimate_low} - $${fare.uber.estimate_high}</span>
                        <span class="rs-eta">${fare.uber.eta_minutes} min</span>
                    </a>
                    <a href="${links.lyft}" target="_blank" class="rideshare-btn lyft-btn">
                        <span class="rs-name">Lyft</span>
                        <span class="rs-fare">$${fare.lyft.estimate_low} - $${fare.lyft.estimate_high}</span>
                        <span class="rs-eta">${fare.lyft.eta_minutes} min</span>
                    </a>
                </div>
                <div class="rideshare-info">
                    ${fare.distance_miles} mi &middot; ~${fare.estimated_drive_minutes} min drive
                </div>
            </div>
        `;
    },

    stepIcon(step, leg, index) {
        const instr = step.instruction.toLowerCase();
        if (instr.includes('elevator')) return '&#9974;';
        if (instr.includes('stairs')) return '&#128694;';
        if (instr.includes('exit')) return '&#128682;';
        if (instr.includes('enter')) return '&#128681;';
        if (instr.includes('rideshare') || instr.includes('pickup')) return '&#128663;';
        if (instr.includes('request') || instr.includes('uber') || instr.includes('lyft')) return '&#128241;';
        if (instr.includes('ride to')) return '&#128663;';
        if (instr.includes('turn right')) return '&#8599;';
        if (instr.includes('turn left')) return '&#8598;';
        if (instr.includes('u-turn')) return '&#8634;';
        if (index === 0) return '&#9679;';
        return '&#8594;';
    },

    clear() {
        this.currentNav = null;
        SinCityMap.clearRoute();
        const resultDiv = document.getElementById('nav-result');
        if (resultDiv) resultDiv.classList.add('hidden');
        document.getElementById('route-start').value = '';
        document.getElementById('route-end').value = '';
    }
};
