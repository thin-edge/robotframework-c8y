# robotframework-c8y

Robot Framework Library for Cumulocity

# Using it

1. Install via pip

    ```sh
    pip install git+https://github.com/reubenmiller/robotframework-c8y.git@0.0.7
    ```

    Or add it to your `requirements.txt` file

    ```sh
    robotframework-c8y @ git+https://github.com/reubenmiller/robotframework-c8y.git@0.0.7
    ```

    Then install it via

    ```sh
    pip install -r requirements.txt
    ```

2. Create a `.env` file with the following environment variables

    ```sh
    C8Y_BASEURL=https://example.tenant.c8y.com
    C8Y_USER=
    C8Y_TENANT=t12345
    C8Y_PASSWORD=""
    ```

3. Create a Robot test `tests/Example.robot`

    ```robot
    *** Settings ***
    Library    Cumulocity

    *** Test Cases ***
    Device initialization sequence
        Device Should Exist                      tedge01
        Device Should Have Installed Software    tedge
        Device Should Have Measurements          minimum=1   type=myCustomMeasurement
    ```

4. Run the test

    ```sh
    robot tests/Example.robot
    ```

## Library docs

Checkout the [Cumulocity Library docs](./Cumulocity/Cumulocity.rst)
