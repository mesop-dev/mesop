import {
  LitElement,
  html,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import 'https://cdn.plot.ly/plotly-2.32.0.min.js';

class PlotlyComponent extends LitElement {
  createRenderRoot() {
    return this;
  }

  firstUpdated() {
    this.renderPlot();
  }

  renderPlot() {
    const trace1 = {
      x: [1, 2, 3, 4, 5],
      y: [10, 15, 13, 17, 21],
      type: 'scatter',
      mode: 'lines+markers',
      marker: {color: 'red'},
      name: 'Line 1',
    };

    const trace2 = {
      x: [1, 2, 3, 4, 5],
      y: [16, 5, 11, 9, 8],
      type: 'scatter',
      mode: 'lines+markers',
      marker: {color: 'blue'},
      name: 'Line 2',
    };

    const data = [trace1, trace2];

    const layout = {
      title: 'Simple Line Chart Example',
      xaxis: {
        title: 'X Axis',
      },
      yaxis: {
        title: 'Y Axis',
      },
    };

    Plotly.newPlot(document.getElementById('plot'), data, layout);
  }

  render() {
    return html`<div id="plot"></div>`;
  }
}

customElements.define('plotly-component', PlotlyComponent);
