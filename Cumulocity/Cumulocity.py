#!/usr/local/bin/python3
"""Cumulocity IoT Robot Framework library
"""

import logging
from typing import List, Union, Dict, Any
import json
import re

from dotmap import DotMap
from dotenv import load_dotenv
from c8y_test_core.assert_operation import AssertOperation
from c8y_test_core.c8y import CustomCumulocityApp
from c8y_test_core.device_management import (
    DeviceManagement,
    create_context_from_identity,
)
from c8y_test_core.models import Software, Configuration, Firmware
from robot.api.deco import keyword, library
from robot.utils.asserts import fail

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from . import _version

    __version__ = _version.version
except Exception:
    __version__ = "0.0.0"

__author__ = "Reuben Miller"


def is_dot_notation(key: str) -> bool:
    return re.match(r"^[\w.\-: ]+$", key, re.IGNORECASE) is not None


ASSERTION_MAPPING = {
    "assert_count": "Device Should Have %s/s",
    "assert_exists": "%s Should Exist",
}


@library(scope="GLOBAL", auto_keywords=False)
class Cumulocity:
    """Cumulocity Robot Framework Library

    Keywords used to interact and make assertions with Cumulocity IoT

    Example:

    The "Device Should Exist" keyword will set the context of the device so that subsequent
    keywords will not need to explicitly set the device that the keyword is related to.

    Example.robot::
        *** Settings ***
        Library    Cumulocity

        *** Test Cases ***
        Device initialization sequence
            Device Should Exist                      tedge01
            Device Should Have Installed Software    tedge
            Device Should Have Measurements          minimum=1   type=myCustomMeasurement
    """

    ROBOT_LISTENER_API_VERSION = 3

    # Default parameter settings
    DEFAULT_TIMEOUT = 30

    # Class-internal parameters
    device_mgmt: DeviceManagement = None
    c8y: CustomCumulocityApp = None

    # Constructor
    def __init__(
        self,
        timeout: str = DEFAULT_TIMEOUT,
    ):
        self.devices = {}
        self._on_cleanup = []
        load_dotenv()

        try:
            self.c8y = CustomCumulocityApp()
        except Exception as ex:
            logger.warning(
                "Could not load Cumulocity API client. Trying to continue. %s",
                ex,
                exc_info=True,
            )

        self.device_mgmt = create_context_from_identity(self.c8y)
        self.device_mgmt.configure_retries(timeout=timeout)

        # pylint: disable=invalid-name
        self.ROBOT_LIBRARY_LISTENER = self

    #
    # Hooks
    #
    def end_suite(self, _data: Any, result: Any):
        """End suite hook which is called by Robot Framework
        when the test suite has finished

        Args:
            _data (Any): Test data
            result (Any): Test details
        """
        for func in self._on_cleanup:
            if callable(func):
                try:
                    func()
                except Exception as ex:
                    logger.warning("Cleanup function failed. error=%s", ex)

        self._on_cleanup.clear()

    #
    # Alarms
    #
    @keyword("Device Should Have Alarm/s")
    def alarm_assert_count(
        self, minimum: int = 1, maximum: int = None, expected_text: str = None, **kwargs
    ) -> List[str]:
        """Assert number of alarms

        Examples:

            | Device Should Have Alarm/s | minimum=1 |
            | Device Should Have Alarm/s | minimum=1 | expected_text=High Temperature |
            | Device Should Have Alarm/s | minimum=1 | type=custom_typeA | fragmentType=signalStrength |

        Args:
            minimum (int, optional): Minimum number of alarms to expect. Defaults to 1.
            maximum (int, optional): Maximum number of alarms to expect. Ignored if set to None.
                Defaults to None.
            expected_text (str, optional): Expected alarm text to match. Defaults to None.

        Returns:
            List[str]: List of measurements as json
        """
        return self._convert_to_json(
            self.device_mgmt.alarms.assert_count(
                min_matches=minimum,
                max_matches=maximum,
                expected_text=expected_text,
                **kwargs,
            )
        )

    @keyword("Device Should Not Have Alarm/s")
    def alarm_assert_no_alarms(self, **kwargs) -> None:
        """Assert that there are no matching alarms

        Examples::

            | Device Should Not Have Alarm/s |
            | Device Should Not Have Alarm/s | expected_text=High Temperature |
            | Device Should Not Have Alarm/s | type=custom_typeA | fragmentType=signalStrength |

        Args:
            **kwargs: Keyword args which are supported by c8y_api library
        """
        self.device_mgmt.alarms.assert_count(
            min_matches=0, max_matches=0, resolved="false", **kwargs
        )

    @keyword("Alarm Should Exist")
    def alarm_assert_exist(self, alarm_id: str, **kwargs):
        """Assert that an alarm id exists

        Args:
            alarm_id (str): Alarm id

        Returns:
            str: Alarm json
        """
        return self._convert_to_json(
            self.device_mgmt.alarms.assert_exists(alarm_id, **kwargs)
        )

    #
    # Events
    #
    @keyword("Device Should Have Event/s")
    def event_assert_count(
        self,
        expected_text: str = None,
        with_attachment: bool = None,
        minimum: int = 1,
        maximum: int = None,
        **kwargs,
    ) -> List[str]:
        """Assert event count

        Args:
            expected_text (str, optional): Match events by text. Defaults to None.
            with_attachment (bool, optional): Match events with an attachment. Defaults to None.
            minimum (int, optional): Minimum number of events to expect. Defaults to 1.
            maximum (int, optional): Maximum number of events to expect. Defaults to None.

        Returns:
            List[str]: List of events as json
        """
        return self._convert_to_json(
            self.device_mgmt.events.assert_count(
                min_matches=minimum,
                max_matches=maximum,
                expected_text=expected_text,
                with_attachment=with_attachment,
                **kwargs,
            )
        )

    @keyword("Event Should Have An Attachment")
    def event_assert_attachment(
        self,
        event_id: str,
        expected_contents: str = None,
        expected_pattern: str = None,
        expected_size_min: int = None,
        expected_md5: str = None,
        encoding: str = None,
        **kwargs,
    ) -> bytes:
        """Assert event attachment

        Args:
            event_id (str): Event id
            expected_contents (str, optional): Expected attachment contents. Defaults to None.
            expected_pattern (str, optional): Expected attachment pattern to match.
                Defaults to None.
            expected_size_min (int, optional): Minimum attachment size to expect.
                Defaults to None.
            expected_md5 (str, optional): Expected md5 checksum or a file that should be used
                to calculated the md5 checksum from. Defaults to None.
            encoding (str, optional): Attachment encoding to use when comparing content.
                Defaults to None.

        Returns:
            bytes: Attachment
        """
        return self.device_mgmt.events.assert_attachment(
            event_id=event_id,
            encoding=encoding,
            expected_contents=expected_contents,
            expected_pattern=expected_pattern,
            expected_size_min=expected_size_min,
            expected_md5=expected_md5,
            **kwargs,
        )

    @keyword("Event Should Not Have An Attachment")
    def event_assert_no_attachment(self, event_id: str, **kwargs):
        """Assert that an event does not have an attachment

        Args:
            event_id (str): Event id
        """
        self.device_mgmt.events.assert_no_attachment(
            event_id=event_id,
            **kwargs,
        )

    #
    # Binaries
    #
    @keyword("Create Inventory Binary")
    def create_inventory_binary(
        self,
        name: str,
        binary_type: str,
        file: str = None,
        contents: str = None,
        **kwargs,
    ) -> str:
        """Create an inventory binary from either a file or a string

        Returns:
            str: Url to the inventory binary
        """
        with self.device_mgmt.binaries.new_binary(
            name, binary_type, file=file, contents=contents, delete=False, **kwargs
        ) as binary_ref:
            self._on_cleanup.append(binary_ref.binary.delete)
            return binary_ref.url

    #
    # Configuration
    #
    @keyword("Should Support Configurations")
    def configuration_assert_supported_types(
        self, *types: str, includes: bool = False, **kwargs
    ) -> List[str]:
        supported_types = self.device_mgmt.configuration.assert_supported_types(
            types, includes=includes, **kwargs
        )
        return supported_types

    @keyword("Get Configuration")
    def get_configuration(self, typename: str, **kwargs):
        operation = self.device_mgmt.configuration.get_configuration(
            Configuration(type=typename),
            **kwargs,
        )
        return operation

    @keyword("Set Configuration")
    def set_configuration(self, typename: str, url: str, **kwargs):
        operation = self.device_mgmt.configuration.set_configuration(
            Configuration(type=typename, url=url),
            **kwargs,
        )
        return operation

    #
    # Software
    #
    def _software_format_list(self, *items: str) -> List[Software]:
        """Convert a list of strings to a list of Software items.
        Each item in the list should be a csv string in the format
        of "<name>,<version>,<url>".

        Leave a blank value if you do not want to set it, e.g. ",1.0.0,"

        Returns:
            List[Software]: List of software
        """
        return [Software(*item.split(",", 3)) for item in items if item]

    @keyword("Device Should Have Installed Software")
    def software_assert_installed(
        self, *expected_software_list: str, mo: str = None, **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """Assert that software packages are installed (in the c8y_SoftwareList fragment)

        Examples:

            | ${software}= | Device Should Have Installed Software | package-001 | package-002,1.0.0 |
            | Length Should Be | ${software} | 1000 |
            | Should Contain | ${software} | package-001 |
            | Should Be Equal | ${software["package-002"]["version"]} | 1.0.0 |

        Args:
            mo (str, optional): Device Managed object. Defaults to None.
                If set to None, then the current device managed object context
                will be used.

        Returns:
            Dict[str, Dict[str, Any]]: Managed object json
        """
        items = self._software_format_list(*expected_software_list)

        return self._convert_to_json(
            self.device_mgmt.software_management.assert_software_installed(
                *items,
                mo=mo,
                **kwargs,
            )
        )

    @keyword("Install Software")
    def software_install(self, *software_list: str, **kwargs) -> AssertOperation:
        """Install software via an operation

        It does not wait for the operation to be completed. Use with the operation
        keywords to check if the operation was successful or not.

        Returns:
            AssertOperation: Operation
        """
        items = self._software_format_list(*software_list)
        operation = self.device_mgmt.software_management.install(
            *items,
            **kwargs,
        )
        return operation

    #
    # Firmware
    #
    @keyword("Install Firmware")
    def firmware_install(
        self, name: str, version: str = "", url: str = "", **kwargs
    ) -> AssertOperation:
        """Install Firmware via an operation

        It does not wait for the operation to be completed. Use with the operation
        keywords to check if the operation was successful or not.

        Args:
            name (str): Firmware name
            version (str, optional): Firmware version
            url (str, optional): Firmware url

        Returns:
            AssertOperation: Operation
        """
        firmware = Firmware(name=name, version=version, url=url)
        operation = self.device_mgmt.firmware_management.install(
            firmware,
            **kwargs,
        )
        return operation

    @keyword("Device Should Have Firmware")
    def firmware_assert_installed(
        self, name: str, version: str = "", url: str = "", **kwargs
    ) -> Dict[str, Any]:
        """Assert that a device as a specific firmware installed

        Args:
            name (str): Firmware name
            version (str, optional): Firmware version
            url (str, optional): Firmware url

        Returns:
            Dict[str, Any]: Managed object
        """
        item = Firmware(name, version, url)
        return self._convert_to_json(
            self.device_mgmt.firmware_management.assert_firmware(item, **kwargs)
        )

    @keyword("Device Should Not Have Firmware")
    def firmware_assert_not_installed(
        self, name: str, version: str = "", url: str = "", **kwargs
    ) -> Dict[str, Any]:
        """Assert that a device as a specific firmware is not installed

        Args:
            name (str): Firmware name
            version (str, optional): Firmware version
            url (str, optional): Firmware url

        Returns:
            Dict[str, Any]: Managed object
        """
        item = Firmware(name, version, url)
        return self._convert_to_json(
            self.device_mgmt.firmware_management.assert_not_firmware(item, **kwargs)
        )

    #
    # Shell
    #
    @keyword("Execute Shell Command")
    def shell_execute_command(self, text: str, **kwargs) -> AssertOperation:
        """Send a shell command to a device via the Cumulocity IoT c8y_Command operation

        Args:
            text (str): Command to execute

        Returns:
            AssertOperation: Operation
        """
        return self.device_mgmt.command.execute(text, **kwargs)

    #
    # Operations
    #
    @keyword("Should Contain Supported Operations")
    def operation_assert_contains_supported_operations(
        self, *types: str, **kwargs
    ) -> Dict[str, Any]:
        """Should contain the given supported operations.

        Additional supported operations that are not included in the assertion
        may exist.

        Examples:
            | ${mo}= | Should Contain Supported Operations | c8y_Restart | c8y_SoftwareUpdate |
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_contains_supported_operations(
                *types, **kwargs
            )
        )

    @keyword("Should Have Exact Supported Operations")
    def operation_assert_supported_operations(
        self, *types: str, **kwargs
    ) -> Dict[str, Any]:
        """Should have exactly the given supported operations.

        Additional supported operations that are not included in the assertion
        may NOT exist.

        Examples:
            | ${mo}= | Should Have Exact Supported Operations | c8y_Restart |
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_supported_operations(*types, **kwargs)
        )

    @keyword("Create Operation")
    def create_operation(
        self,
        fragments: Union[Dict[str, Any], str],
        description="Custom operation",
        **kwargs,
    ) -> AssertOperation:
        """Create an operation using provided fragments.

        This keyword can be used to create any Cumulocity operation as it does not assume the data structure.

        It does not wait for the operation to be completed. Use with the operation
        keywords to check if the operation was successful or not.

        Examples:
            | ${operation}= | Create Operation | fragments={"c8y_Command":{"text":"ls -l"}} |
            | ${operation}= | Create Operation | fragments={"c8y_Command":{"text":"ls -l"}} | description=Send shell operation |
            | ${operation}= | Create Operation | fragments={"c8y_Command":{"text":"ls -l"}} | otherInfo=foobar |

        Args:
            fragments (Union[Dict[str, Any], str]): Fragments to be included in the operation body.
                If a string is provided it will be parsed as json. Defaults to {}
            description (str, optional): Description. Defaults to 'Custom operation'

        Returns:
            AssertOperation: Operation
        """
        if fragments is None:
            fragments = {}

        if isinstance(fragments, str):
            fragments = json.loads(fragments)

        op_fragments = {"description": description, **fragments, **kwargs}
        operation = self.device_mgmt.create_operation(
            **op_fragments,
        )
        return operation

    @keyword("Operation Should Be SUCCESSFUL")
    def operation_assert_success(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation is set to SUCCESSFUL

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_success(**kwargs))

    @keyword("Operation Should Be PENDING")
    def operation_assert_pending(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation is set to PENDING

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_pending(**kwargs))

    @keyword("Operation Should Not Be PENDING")
    def operation_assert_not_pending(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation is not set to PENDING

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_not_pending(**kwargs))

    @keyword("Operation Should Be DONE")
    def operation_assert_done(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation is set to either SUCCESSFUL or FAILED
        (e.g. a final state)

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_done(**kwargs))

    @keyword("Operation Should Not Be DONE")
    def operation_assert_not_done(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation is not set to either SUCCESSFUL or FAILED
        (e.g. a final state)

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_not_done(**kwargs))

    @keyword("Operation Should Be EXECUTING")
    def operation_assert_executing(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation is set to EXECUTING

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_executing(**kwargs))

    @keyword("Operation Should Be DELIVERED")
    def operation_assert_delivered(self, operation: AssertOperation, **kwargs) -> str:
        """Assert that the operation has been delivered via MQTT.
        Only works if the agent is subscribed to the operations via mqtt

        Args:
            operation (AssertOperation): Operation

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(operation.assert_delivered(**kwargs))

    @keyword("Operation Should Be FAILED")
    def operation_assert(
        self, operation: AssertOperation, failure_reason: str = ".+", **kwargs
    ) -> str:
        """Assert that the operation is set to FAILED

        Args:
            operation (AssertOperation): Operation
            failure_reason (str, optional): Expected failure reason pattern.
                Defaults to ".+" it is best practice to always include a
                failure reason when setting to FAILED.

        Returns:
            str: Operation as json
        """
        return self._convert_to_json(
            operation.assert_failed(failure_reason=failure_reason, **kwargs)
        )

    #
    # Trusted Certificates
    #
    @keyword("Delete Device Certificate From Platform")
    def trusted_certificate_delete(self, fingerprint: str, **kwargs):
        """Delete the trusted certificate from the platform

        Args:
            fingerprint (str): Certificate fingerprint
        """
        self.device_mgmt.trusted_certificates.delete_certificate(
            fingerprint,
            **kwargs,
        )

    def _convert_item(self, item: any) -> Dict[str, Any]:
        if not item:
            return ""

        data = item
        if item and hasattr(item, "to_json"):
            data = item.to_json()
            if data and hasattr(item, "id"):
                data["id"] = item.id

        return data

    def _convert_to_json(self, item: any) -> Union[str, List[str]]:
        if isinstance(item, list):
            return [self._convert_item(subitem) for subitem in item]

        return self._convert_item(item)

    #
    # Library settings
    #
    @keyword("Set API Timeout")
    def set_timeout(self, timeout: float = 30):
        """Set global assertion timeout

        This controls the default timeout when an assertion should
        be given up on.

        Args:
            timeout (float, optional): Timeout in seconds. Defaults to 30.
        """
        self.device_mgmt.configure_retries(timeout=timeout)

    #
    # Devices / Child devices
    #
    def _set_managed_object_context(
        self, external_id: str = None, external_type: str = "c8y_Serial", **kwargs
    ):
        """Set the managed object context which will be used for subsequent keywords

        Args:
            external_id (str, optional): External identity. Defaults to None.
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            str: Managed object json
        """
        identity = self.device_mgmt.identity.assert_exists(
            external_id, external_type, **kwargs
        )
        self.device_mgmt.set_device_id(identity.id)

        return self._convert_to_json(
            self.device_mgmt.inventory.assert_exists(identity.id),
        )

    @keyword("Set Device")
    def set_device(
        self, external_id: str = None, external_type: str = "c8y_Serial", **kwargs
    ) -> Dict[str, Any]:
        """
        Deprecated: This function will be removed in the future. Please use "Set Managed Object" instead.

        Set the device context which will be used for subsequent keywords

        Args:
            external_id (str, optional): External identity. Defaults to None.
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            Dict[str, Any]: Managed object json
        """
        return self._set_managed_object_context(
            external_id=external_id, external_type=external_type, **kwargs
        )

    @keyword("Set Managed Object")
    def set_managed_object(
        self, external_id: str = None, external_type: str = "c8y_Serial", **kwargs
    ) -> Dict[str, Any]:
        """Set the managed object context which will be used for subsequent keywords

        Args:
            external_id (str, optional): External identity. Defaults to None.
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            Dict[str, Any]: Managed object json
        """
        return self._set_managed_object_context(
            external_id=external_id, external_type=external_type, **kwargs
        )

    @keyword("Device Should Have A Child Devices")
    def assert_child_device_names(self, *name: str, **kwargs) -> List[str]:
        """Assert the presence of child devices and their matching names

        Returns:
            List[str]: List of child devices json
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_child_device_names(*name, **kwargs)
        )

    @keyword("Device Should Have Measurements")
    def assert_measurement_count(
        self, minimum: int = 1, maximum: int = None, **kwargs
    ) -> List[str]:
        """Assert measurement count

        Args:
            minimum (int, optional): Minimum number of events to expect. Defaults to 1.
            maximum (int, optional): Maximum number of events to expect. Defaults to None.

        Returns:
            List[str]: List of measurements as json

        Example:
            |             | Command                         |   |                                                                              Result                                                                                                  |
            | ${measure}= | Device Should Have Measurements | 1 | ${measure} = [{'type': 'c8y_TemperatureMeasurement', 'time': '2023-02-02T13:30:16.343Z', 'c8y_TemperatureMeasurement': {'T': {'unit': 'C', 'value': 20}}, 'source': {'id': '55207'}}] |
        """
        try:
            return self._convert_to_json(
                self.device_mgmt.measurements.assert_count(
                    min_count=minimum, max_count=maximum, **kwargs
                )
            )
        except AssertionError as ex:
            fail(f"not enough measurements were found. args={ex.args}")

    @keyword("Delete Managed Object and Device User")
    def delete_managed_object(
        self, external_id: str, external_id_type: str = "c8y_Serial", **kwargs
    ):
        """Delete managed object and related device user

        Args:
            external_id (str): External identity
            external_id_type (str, optional): External identity type. Defaults to "c8y_Serial".
        """
        managed_object = self.device_mgmt.identity.assert_exists(
            external_id, external_type=external_id_type, **kwargs
        )
        self.device_mgmt.inventory.delete_device_and_user(managed_object)

    @keyword("Device Should Have Fragments")
    def assert_contains_fragments(self, *fragments: str, **kwargs) -> str:
        """Assert that a device contains specific fragments

        Returns:
            str: Managed object json
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_contains_fragments(fragments, **kwargs)
        )

    @keyword("Device Should Have Fragment Values")
    def assert_contains_fragment_values(
        self, *properties: str, **kwargs
    ) -> Dict[str, Any]:
        """Assert that a managed object contains specific fragment values.

        It supports referencing nested fragments via dot notation.

        Examples:
            | Device Should Have Fragment Values | status=down |
            | Device Should Have Fragment Values | status=down | c8y_Hardware.serialNumber="abcdef 01234" |

        Args:
            properties (List[str]): List of key/values which correspond to fragments
                and their values that are expected to be present

        Returns:
            Dict[str, Any]: Managed object
        """

        value_dict = self._create_dict(properties)
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_contains_fragment_values(
                value_dict, **kwargs
            )
        )

    def _create_dict(self, properties: List[Union[str, dict]]) -> dict:
        values = DotMap()
        for item in properties:
            if isinstance(item, str):
                if item.startswith("{") and item.endswith("}"):
                    obj = json.loads(item)

                    value_dict = DotMap(
                        {
                            **value_dict,
                            **obj,
                        }
                    )
                else:
                    key, _, value = str(item).partition("=")
                    key = key.strip()
                    value = value.strip()

                    # Try to parse value to a type, fallback to a string
                    try:
                        typed_value = json.loads(value)
                    except json.decoder.JSONDecodeError:
                        typed_value = str(value)

                    if key and is_dot_notation(key):
                        # Assign nested path
                        tmp = values
                        key_parts = key.split(".")
                        for k in key_parts[:-1]:
                            tmp = tmp[k]

                        tmp[key_parts[-1]] = typed_value
                    elif isinstance(typed_value, dict):
                        values = DotMap(
                            {
                                **values,
                                **typed_value,
                            }
                        )
                    else:
                        raise ValueError(
                            "Value type not supported. Please set a string, number, boolean, or object"
                        )

            elif isinstance(item, dict):
                value_dict = DotMap(
                    {
                        **value_dict,
                        **obj,
                    }
                )
            else:
                raise ValueError(
                    "Value type not supported. Only str and dictionaries are supported as properties"
                )

        return values.toDict()

    @keyword("Should Be A Child Device Of Device")
    def assert_child_device_relationship(
        self, external_id: str, external_id_type: str = "c8y_Serial", **kwargs
    ) -> str:
        """Assert that a child device (referenced via external identity)
        should be a child device of the current device context.

        Returns:
            str: Managed object json
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_relationship(
                external_id, external_id_type, child_type="childDevices", **kwargs
            )
        )

    @keyword("Restart Device")
    def restart_device(self, **kwargs) -> str:
        """Restart the device via an operation

        It does not wait for the operation to be completed. Use with the operation
        keywords to check if the operation was successful or not.

        Returns:
            AssertOperation: Operation
        """
        return self.device_mgmt.restart(**kwargs)

    def _managed_object_exists(
        self,
        external_id: str,
        external_type: str = "c8y_Serial",
        show_info: bool = True,
        **kwargs,
    ):
        identity = self.device_mgmt.identity.assert_exists(
            external_id, external_type, **kwargs
        )
        self.device_mgmt.set_device_id(identity.id)

        if show_info:
            mgmt_url = "/".join(
                [
                    self.device_mgmt.c8y.base_url,
                    "apps/devicemanagement/index.html#/device",
                    identity.id,
                    "control",
                ]
            )
            logger.info("-" * 60)
            logger.info("EXTERNAL SERIAL  : %s", external_id)
            logger.info("EXTERNAL ID      : %s", identity.id)
            logger.info("EXTERNAL URL     : %s", mgmt_url)
            logger.info("-" * 60)

        return self._convert_to_json(self.device_mgmt.inventory.assert_exists())

    @keyword("Device Should Exist")
    def device_should_exist(
        self,
        external_id: str,
        external_type: str = "c8y_Serial",
        show_info: bool = True,
        **kwargs,
    ) -> str:
        """
        Deprecated: Please use "External Identity Should Exist" instead
        Assert that a device exists by checking its external identity

        Args:
            external_id (str): External identity
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            str: Managed object json
        """
        return self._managed_object_exists(
            external_id, external_type, show_info, **kwargs
        )

    @keyword("External Identity Should Exist")
    def managed_object_should_exist(
        self,
        external_id: str,
        external_type: str = "c8y_Serial",
        show_info: bool = True,
        **kwargs,
    ) -> str:
        """Assert that an external identity exists. It will return the associated managed object

        Args:
            external_id (str): External identity
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            str: Managed object json
        """
        return self._managed_object_exists(
            external_id, external_type, show_info, **kwargs
        )

    @keyword("Log Device Info")
    def show_device_information(self, device_id: str = None, **kwargs):
        """Show device information, e.g. id, external id and a link to the
        device in Cumulocity IoT.

        By default it will use the current device context, however you can
        still specify your own managed object id.

        Args:
            device_id (str, optional): Managed object id to use as reference.
                If set to None, then the current context will be used.
        """
        if device_id is None:
            device_id = self.device_mgmt.context.device_id

        if not device_id:
            logger.warning("No device has been set, nothing to do")
            return

        managed_object = self.device_mgmt.inventory.assert_exists(device_id, **kwargs)

        external_id = str(managed_object.owner)
        if external_id.startswith("device_"):
            external_id = external_id[7:]

        mgmt_url = "/".join(
            [
                self.device_mgmt.c8y.base_url,
                "apps/devicemanagement/index.html#/device",
                managed_object.id,
                "control",
            ]
        )

        logger.info("-" * 60)
        logger.info("DEVICE SERIAL  : %s", external_id)
        logger.info("DEVICE ID      : %s", managed_object.id)
        logger.info("DEVICE TYPE    : %s", managed_object.type)
        logger.info("DEVICE URL     : %s", mgmt_url)
        logger.info("-" * 60)

    @keyword("Should Have Services")
    def assert_services(
        self,
        device_id: str = None,
        min_count: int = 1,
        max_count: int = None,
        service_type: str = None,
        status: str = None,
        name: str = None,
        **kwargs,
    ):
        """Device should have a specific count of service matching the given criteria

        Args:
            device_id (str, optional): Managed object id to use as reference.
                If set to None, then the current context will be used.
            min_count (int, optional): Minimum number of service matches (inclusive)
            max_count (int, optional): Maximum number of service matches (inclusive)
            service_type (str, optional): Filter by service type
            name (str, optional): Filter by service name
            status (str, optional): Filter by service status
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_services(
                inventory_id=device_id,
                min_count=min_count,
                max_count=max_count,
                service_type=service_type,
                name=name,
                status=status,
                **kwargs,
            )
        )


if __name__ == "__main__":
    pass
