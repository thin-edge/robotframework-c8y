Cumulocity
==========
Scope:    GLOBAL

Cumulocity Robot Framework Library

Keywords used to interact and make assertions with Cumulocity IoT

Example:

The "Device Should Exist" keyword will set the context of the device so that
subsequent
keywords will not need to explicity set the device that the keyword is related
to.

Example.robot::
    *** Settings ***
    Library    Cumulocity

    *** Test Cases ***
    Device initialization sequence
        Device Should Exist                      tedge01
        Device Should Have Installed Software    tedge
        Device Should Have Measurements          minimum=1
type=myCustomMeasurement

Importing
---------
Arguments:  [timeout: str = 30]

Initialize self.  See help(type(self)) for accurate signature.

Alarm Should Exist
------------------
Arguments:  [alarm_id: str, **kwargs]

Assert that an alarm id exists

Args:
    alarm_id (str): Alarm id

Returns:
    str: Alarm json

Delete Device Certificate From Platform
---------------------------------------
Arguments:  [fingerprint: str, **kwargs]

Delete the trusted certificate from the platform

Args:
    fingerprint (str): Certificate fingerprint

Delete Managed Object and Device User
-------------------------------------
Arguments:  [external_id: str, external_id_type: str = c8y_Serial]

Delete managed object and related device user

Args:
    external_id (str): External identity
    external_id_type (str, optional): External identity type. Defaults to
"c8y_Serial".

Device Should Exist
-------------------
Arguments:  [external_id: str, external_type: str = c8y_Serial, show_info:
            bool = True]

Assert that a device exists by checking its external identity

Args:
    external_id (str): External identity
    external_type (str, optional): External identity type. Defaults to
"c8y_Serial".

Returns:
    str: Managed object json

Device Should Have A Child Devices
----------------------------------
Arguments:  [*name: str]

Assert the presence of child devices and their matching names

Returns:
    List[str]: List of child devices json

Device Should Have Alarm/s
--------------------------
Arguments:  [minimum: int = 1, expected_text: str | None = None, **kwargs]

Assert number of alarms

Examples::

    | Device Should Have Alarm/s | minimum=1 |
    | Device Should Have Alarm/s | minimum=1 | expected_text=High Temperature
|
    | Device Should Have Alarm/s | minimum=1 | type=custom_typeA |
fragmentType=signalStrength |

Args:
    minimum (int, optional): Minimum number of alarms to expect. Defaults to
1.
    expected_text (str, optional): Expected alarm text to match. Defaults to
None.

Returns:
    List[str]: List of measurements as json

Device Should Have Event/s
--------------------------
Arguments:  [expected_text: str | None = None, with_attachment: bool | None =
            None, minimum: int = 1, maximum: int | None = None, **kwargs]

Assert event count

Args:
    expected_text (str, optional): Match events by text. Defaults to None.
    with_attachment (bool, optional): Match events with an attachment.
Defaults to None.
    minimum (int, optional): Minimum number of events to expect. Defaults to
1.
    maximum (int, optional): Maximum number of events to expect. Defaults to
None.

Returns:
    List[str]: List of events as json

Device Should Have Fragments
----------------------------
Arguments:  [*fragments: str]

Assert that a device contains specific fragments

Returns:
    str: Managed object json

Device Should Have Installed Software
-------------------------------------
Arguments:  [*expected_software_list: str, mo: str | None = None, **kwargs]

Assert that software packages are installed (in the c8y_SoftwareList fragment)

Args:
    mo (str, optional): Device Managed object. Defaults to None.
        If set to None, then the current device managed object context
        will be used.

Returns:
    str: Managed object json

Device Should Have Measurements
-------------------------------
Arguments:  [minimum: int = 1, maximum: int | None = None, **kwargs]

Assert measurement count

Args:
    minimum (int, optional): Minimum number of events to expect. Defaults to
1.
    maximum (int, optional): Maximum number of events to expect. Defaults to
None.

Returns:
    List[str]: List of measurements as json

Event Should Have An Attachment
-------------------------------
Arguments:  [event_id: str, expected_contents: str | None = None,
            expected_pattern: str | None = None, expected_size_min: int | None
            = None, encoding: str | None = None, **kwargs]

Assert event attachment

Args:
    event_id (str): Event id
    expected_contents (str, optional): Expected attachment contents. Defaults
to None.
    expected_pattern (str, optional): Expected attachment pattern to match.
        Defaults to None.
    expected_size_min (int, optional): Minimum attachment size to expect.
        Defaults to None.
    encoding (str, optional): Attachment encoding to use when comparing
content.
        Defaults to None.

Returns:
    bytes: Attachment

Event Should Not Have An Attachment
-----------------------------------
Arguments:  [event_id: str, **kwargs]

Assert that an event does not have an attachment

Args:
    event_id (str): Event id

Install Software
----------------
Arguments:  [*software_list: str, **kwargs]

Install software via an operation

It does not wait for the operation to be completed. Use with the operation
keywords to check if the operation was successful or not.

Returns:
    AssertOperation: Operation

Operation Should Be DONE
------------------------
Arguments:  [operation: AssertOperation, **kwargs]

Assert that the operation is set to either SUCCESSFUL or FAILED
(e.g. a final state)

Args:
    operation (AssertOperation): Operation

Returns:
    str: Operation as json

Operation Should Be FAILED
--------------------------
Arguments:  [operation: AssertOperation, failure_reason: str = .+, **kwargs]

Assert that the operation is set to FAILED

Args:
    operation (AssertOperation): Operation
    failure_reason (str, optional): Expected failure reason pattern.
        Defaults to ".+" it is best practice to always include a
        failure reason when setting to FAILED.

Returns:
    str: Operation as json

Operation Should Be PENDING
---------------------------
Arguments:  [operation: AssertOperation, **kwargs]

Assert that the operation is set to PENDING

Args:
    operation (AssertOperation): Operation

Returns:
    str: Operation as json

Operation Should Be SUCCESSFUL
------------------------------
Arguments:  [operation: AssertOperation, **kwargs]

Assert that the operation is set to SUCCESSFUL

Args:
    operation (AssertOperation): Operation

Returns:
    str: Operation as json

Operation Should Not Be PENDING
-------------------------------
Arguments:  [operation: AssertOperation, **kwargs]

Assert that the operation is not set to PENDING

Args:
    operation (AssertOperation): Operation

Returns:
    str: Operation as json

Set API Timeout
---------------
Arguments:  [timeout: float = 30]

Set global assertion timeout

This controls the default timeout when an assertion should
be given up on.

Args:
    timeout (float, optional): Timeout in seconds. Defaults to 30.

Set Device
----------
Arguments:  [external_id: str | None = None, external_type: str = c8y_Serial]

Set the device context which will be used for subsequent keywords

Args:
    external_id (str, optional): External identity. Defaults to None.
    external_type (str, optional): External identity type. Defaults to
"c8y_Serial".

Returns:
    str: Managed object json

Should Be A Child Device Of Device
----------------------------------
Arguments:  [external_id: str, external_id_type: str = c8y_Serial]

Assert that a child device (referenced via external identity)
should be a child device of the current device context.

Returns:
    str: Managed object json

