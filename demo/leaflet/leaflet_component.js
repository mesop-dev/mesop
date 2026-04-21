// leaflet_map_component.js
import {
  LitElement,
  html,
  css,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'; // Leaflet CDN

export class LeafletMapComponent extends LitElement {
  static properties = {
    center: {type: Array}, // Expecting [latitude, longitude]
    zoom: {type: Number},
    markers: {type: Array}, // Array of marker objects
    clickEvent: {type: String}, // Event handler ID for clicks
  };

  static styles = css`
    #map {
      height: 400px; /* Adjust map height as needed */
      width: 100%;
    }
  `;

  constructor() {
    super();
    this.center = [0.0, 0.0];
    this.zoom = 13;
    this.markers = [];
    this.clickEvent = '';
    this._map = null; // Internal Leaflet map instance
  }

  firstUpdated() {
    this._initializeMap();
  }

  updated(changedProperties) {
    if (changedProperties.has('center') || changedProperties.has('zoom')) {
      this._updateMapView();
    }
    if (changedProperties.has('markers')) {
      this._updateMarkers();
    }
  }

  _initializeMap() {
    if (this._map) return; // Prevent re-initialization

    this._map = L.map(this.shadowRoot.querySelector('#map')).setView(
      this.center,
      this.zoom,
    );

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(this._map);

    this._map.on('click', (event) => {
      if (this.clickEvent) {
        this.dispatchEvent(
          new MesopEvent(this.clickEvent, {
            latlng: [event.latlng.lat, event.latlng.lng], // Send latlng back to Python
          }),
        );
      }
    });

    this._updateMarkers(); // Initial marker rendering
  }

  _updateMapView() {
    if (this._map) {
      this._map.setView(this.center, this.zoom);
    }
  }

  _updateMarkers() {
    if (!this._map) return;

    // Clear existing markers
    if (this._markerLayer) {
      this._map.removeLayer(this._markerLayer);
    }
    this._markerLayer = L.layerGroup().addTo(this._map); // Layer group for efficient marker management

    this.markers.forEach((markerData) => {
      const marker = L.marker(markerData.latlng);
      if (markerData.popup_content) {
        marker.bindPopup(markerData.popup_content);
      }
      marker.addTo(this._markerLayer);
    });
  }

  render() {
    return html`
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <div id="map"></div>
    `;
  }
}

customElements.define('leaflet-map-component', LeafletMapComponent);
