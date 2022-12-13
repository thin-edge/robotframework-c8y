#!/usr/local/bin/python3
"""Cumulocity IoT Robot Framework library
"""

import json
import logging
from typing import List, Union

from dotenv import load_dotenv
from c8y_test_core.assert_operation import AssertOperation
from c8y_test_core.c8y import CustomCumulocityApp
from c8y_test_core.device_management import DeviceManagement, create_context_from_identity
from c8y_test_core.models import Software
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
    keywords will not need to explicity set the device that the keyword is related to.

    Example.robot::
        *** Settings ***
        Library    Cumulocity

        *** Test Cases ***
        Device initialization sequence
            Device Should Exist                      tedge01
            Device Should Have Installed Software    tedge
            Device Should Have Measurements          minimum=1   type=myCustomMeasurement
    """

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
        load_dotenv()

        try:
            self.c8y = CustomCumulocityApp()
        except Exception as ex:
            logger.warning("Could not load Cumulocity API client. Trying to continue. %s", ex)

        self.device_mgmt = create_context_from_identity(self.c8y)
        self.device_mgmt.configure_retries(timeout=timeout)

    #
    # Alarms
    #
    @keyword("Device Should Have Alarm/s")
    def alarm_assert_count(
        self, minimum: int = 1, expected_text: str = None, **kwargs
    ) -> List[str]:
        """Assert number of alarms

        Examples::

            | Device Should Have Alarm/s | minimum=1 |
            | Device Should Have Alarm/s | minimum=1 | expected_text=High Temperature |
            | Device Should Have Alarm/s | minimum=1 | type=custom_typeA | fragmentType=signalStrength |

        Args:
            minimum (int, optional): Minimum number of alarms to expect. Defaults to 1.
            expected_text (str, optional): Expected alarm text to match. Defaults to None.

        Returns:
            List[str]: List of measurements as json
        """
        return self._convert_to_json(
            self.device_mgmt.alarms.assert_count(
                min_matches=minimum, expected_text=expected_text, **kwargs
            )
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
    ) -> str:
        """Assert that software packages are installed (in the c8y_SoftwareList fragment)

        Args:
            mo (str, optional): Device Managed object. Defaults to None.
                If set to None, then the current device managed object context
                will be used.

        Returns:
            str: Managed object json
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
    # Operations
    #
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

    def _convert_item(self, item: any) -> str:
        if not item:
            return ""

        data = item
        if item and hasattr(item, "to_json"):
            data = item.to_json()

        return json.dumps(data)

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
    @keyword("Set Device")
    def set_device(
        self, external_id: str = None, external_type: str = "c8y_Serial"
    ) -> str:
        """Set the device context which will be used for subsequent keywords

        Args:
            external_id (str, optional): External identity. Defaults to None.
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            str: Managed object json
        """

        identity = self.device_mgmt.identity.assert_exists(external_id, external_type)
        self.device_mgmt.set_device_id(identity.id)

        return self._convert_to_json(
            self.device_mgmt.inventory.assert_exists(identity.id),
        )

    @keyword("Device Should Have A Child Devices")
    def assert_child_device_names(self, *name: str) -> List[str]:
        """Assert the presence of child devices and their matching names

        Returns:
            List[str]: List of child devices json
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_child_device_names(*name)
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
        self, external_id: str, external_id_type: str = "c8y_Serial"
    ):
        """Delete managed object and related device user

        Args:
            external_id (str): External identity
            external_id_type (str, optional): External identity type. Defaults to "c8y_Serial".
        """
        managed_object = self.device_mgmt.identity.assert_exists(
            external_id, external_type=external_id_type
        )
        self.device_mgmt.inventory.delete_device_and_user(managed_object)

    @keyword("Device Should Have Fragments")
    def assert_contains_fragments(self, *fragments: str) -> str:
        """Assert that a device contains specific fragments

        Returns:
            str: Managed object json
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_contains_fragments(fragments)
        )

    @keyword("Should Be A Child Device Of Device")
    def assert_child_device_relationship(
        self, external_id: str, external_id_type: str = "c8y_Serial"
    ) -> str:
        """Assert that a child device (referenced via external identity)
        should be a child device of the current device context.

        Returns:
            str: Managed object json
        """
        return self._convert_to_json(
            self.device_mgmt.inventory.assert_relationship(
                external_id, external_id_type, child_type="childDevices"
            )
        )

    @keyword("Device Should Exist")
    def assert_device_exists(
        self,
        external_id: str,
        external_type: str = "c8y_Serial",
        show_info: bool = True,
    ) -> str:
        """Assert that a device exists by checking its external identity

        Args:
            external_id (str): External identity
            external_type (str, optional): External identity type. Defaults to "c8y_Serial".

        Returns:
            str: Managed object json
        """
        identity = self.device_mgmt.identity.assert_exists(external_id, external_type)
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
            logger.info("DEVICE SERIAL  : %s", external_id)
            logger.info("DEVICE ID      : %s", identity.id)
            logger.info("DEVICE URL     : %s", mgmt_url)
            logger.info("-" * 60)

        return self._convert_to_json(self.device_mgmt.inventory.assert_exists())


if __name__ == "__main__":
    pass
