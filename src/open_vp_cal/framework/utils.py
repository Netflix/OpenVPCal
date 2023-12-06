import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Union

import requests

from open_vp_cal.core import constants
from open_vp_cal.core.resource_loader import ResourceLoader


def log_results(data: Dict) -> Union[requests.Response, None]:
    """ Logs the usage stats

    Args:
        data: The data containing the calibration settings, samples, and the results

    """
    if os.getenv(constants.OPEN_VP_CAL_UNIT_TESTING):
        return None

    try:
        import open_vp_cal

        utc_now = datetime.now(timezone.utc)
        utc_string = utc_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        data_dict = {
            "job_id": str(uuid.uuid4()),
            "version": open_vp_cal.__version__,
            "utc": utc_string,
            "data": json.dumps(data)
        }
        logging_bin = ResourceLoader.logging()
        with open(logging_bin, 'rb') as file:
            read_encoded = file.read()
            logging_route = base64.b64decode(read_encoded).decode('utf-8')
            response = requests.post(logging_route, data=json.dumps(data_dict))
            return response
    except Exception:
        pass
    return None
