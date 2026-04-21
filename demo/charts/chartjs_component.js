import {
  LitElement,
  html,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import 'https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js';

class ChartjsComponent extends LitElement {
  static properties = {
    config: {type: String},
  };

  constructor() {
    super();
    this.chart = null;
  }

  createRenderRoot() {
    return this;
  }

  firstUpdated() {
    this.renderChart();
  }

  updated(changedProperties) {
    if (changedProperties.has('config')) {
      this.renderChart();
    }
  }

  renderChart() {
    if (this.chart) {
      this.chart.destroy();
    }
    const ctx = this.querySelector('#chart');
    this.chart = new Chart(ctx, JSON.parse(this.config));
  }

  render() {
    return html`<canvas id="chart"></canvas>`;
  }
}

customElements.define('chartjs-component', ChartjsComponent);
