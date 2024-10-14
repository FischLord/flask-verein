"""

Utility methods for the config
----------------

"""


def eval_bool_env_var(env_var) -> bool:
    """Evaluates a boolean or string environment variable

    :param env_var: The environment variable to evaluate (str or bool)
    :return: The evaluated boolean value
    """
    # If it's already a boolean, return it directly
    if isinstance(env_var, bool):
        return env_var
    # Otherwise, assume it's a string and evaluate it
    return True if env_var.lower() in ("true", "t", "1") else False
