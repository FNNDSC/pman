from unittest.mock import patch, Mock
import functools


def patch_cromwell_api(method_name: str, response_text: str):
    """
    Patch a function of :class:`cromwell_tools.cromwell_api.CromwellAPI`
    so that it returns the given data.

    :param method_name: the function to patch
    :param response_text: the text the mock should respond with
    """
    res = Mock()
    res.text = response_text

    def decorator(real_method):
        @functools.wraps(real_method)
        @patch(f'cromwell_tools.cromwell_api.CromwellAPI.{method_name}')
        def wrapper(self, mock_cromwell_method: Mock, *args, **kwargs):
            mock_cromwell_method.return_value = res
            real_method(self, mock_cromwell_method, *args, **kwargs)
        return wrapper
    return decorator
