from pytest_bdd import scenarios

from tests.shared_utils.shared_steps import *  # noqa

from .step_defs.enrolment_steps import *  # noqa
from .step_defs.shared_steps import *  # noqa

scenarios("./features/enrolment")
