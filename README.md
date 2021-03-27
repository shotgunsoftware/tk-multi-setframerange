[![Python 2.6 2.7 3.7](https://img.shields.io/badge/python-2.6%20%7C%202.7%20%7C%203.7-blue.svg)](https://www.python.org/)
[![Build Status](https://dev.azure.com/shotgun-ecosystem/Toolkit/_apis/build/status/Apps/tk-multi-setframerange?branchName=master)](https://dev.azure.com/shotgun-ecosystem/Toolkit/_build/latest?definitionId=51&branchName=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting](https://img.shields.io/badge/PEP8%20by-Hound%20CI-a873d1.svg)](https://houndci.com)


## Set Frame Range app
This has been forked from Shotgun's GitHub tk-multi-setframerange.

- Works in Maya only.
- Loads no matter if there is a scene open or not.
- Accepts an entity dictionary consisting of 'id' and 'type'.
- If a valid entity, Shot, is found then the "Head In", "Cut In", "Cut Out", and "Tail Out" field values for the given entity (Shot) will be returned.
- The timeline will be updated if the values are different than the Shotgun values.
- "Head In" updates Maya timeline animation start.
- "Cut In" updates Maya timeline minTime and render start.
- "Cut Out" updates Maya timeline maxTime and render end.
- "Tail Out" updates Maya timeline animation end.

### Incorporating in other apps
**checkio**

This code assumes a file is open and contains the `dvs_root` data node. The entity will be filled in automatically if the `dvs_root` node is a valid Shot entity and id.

```
# set frame range
import sgtk
engine = sgtk.platform.current_engine()
if 'dvs-multi-setframerange' in engine.apps.keys():
    engine.apps['ds-multi-setframerange'].run_app()
```

### python console/script editor
```
# set frame range
import sgtk
engine = sgtk.platform.current_engine()
if 'dvs-multi-setframerange' in engine.apps.keys():
    entity_id = int()
    engine.apps['ds-multi-setframerange'].run_app(entity={'id': entity_id, 'type': 'Shot')
```
