import json
from typing import Any

import mesop as me


@me.web_component(path="./chartjs_component.js")
def chartjs_component(config: dict[str, Any]):
  """Creates a Chart.js chart within a Mesop application.

  This components provides a minimal interface to chartjs from Mesop. Right now we
  can only provide the most basic functionality. More complicated functionality is
  not yet supported since they require javascript to work.

  Args:
    config: A dictionary containing the configuration for the Chart.js chart.
        This should follow the standard Chart.js configuration format, but
        note that function properties are not supported and all values must
        be JSON serializable. See the Chart.js documentation for details
        on available options: https://www.chartjs.org/docs/latest/

  Returns:
    A Mesop web component representing the Chart.js chart.
  """
  return me.insert_web_component(
    name="chartjs-component", properties={"config": json.dumps(config)}
  )
