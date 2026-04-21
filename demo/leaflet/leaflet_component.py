from typing import Any, Callable, Dict, List, Tuple

import mesop as me


@me.web_component(path="./leaflet_component.js")
def leaflet_map_component(
  *,
  center: Tuple[float, float] = (0.0, 0.0),  # [latitude, longitude]
  zoom: int = 13,
  markers: List[Dict[str, Any]] | None = None,  # List of marker objects
  on_click: Callable[[me.WebEvent], Any] | None = None,
  key: str | None = None,
):
  """
  A web component wrapper for a Leaflet map.

  Args:
      center: Initial map center as a tuple (latitude, longitude).
      zoom: Initial map zoom level.
      markers: A list of marker objects, each a dictionary with keys:
          - latlng: Tuple (latitude, longitude) for marker position.
          - popup_content: String content for the marker's popup (optional).
      on_click: Callback function when the map is clicked (optional).
      key: Unique key for the component.
  """
  events = {"clickEvent": on_click}

  properties = {
    "center": center,
    "zoom": zoom,
    # Ensure markers is always a list (empty if None)
    "markers": markers if markers else [],
  }

  return me.insert_web_component(
    name="leaflet-map-component",
    key=key,
    events=events,
    properties=properties,
  )
