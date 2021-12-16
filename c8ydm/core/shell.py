#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors

SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import re
from typing import Tuple
from subprocess import Popen, PIPE, TimeoutExpired

class CommandAlias:
    """Command alias class to create an alias for existing command
    """
    def __init__(self,
                 alias: str,
                 command: str,
                 usage: str = '',
                 use_stdout: bool = True,
                 use_stderr: bool = True):
        self._alias = alias
        self._command = command
        self._usage = usage
        self._use_stdout = use_stdout
        self._use_stderr = use_stderr

    def show_usage(self) -> str:
        """Show the command usage

        Returns:
            str: Usage string
        """
        if self._usage:
            return self._usage
        return self._alias

    def transform_command(self, alias: str) -> str:
        """Transform the command alias to the actual command that will be executed

        Args:
            alias (str): Command alias

        Returns:
            str: Command to be executed
        """
        if alias:
            return self._command
        return ''

    def is_match(self, alias: str) -> bool:
        """Check if the given alias matches the current command

        Args:
            alias (str): [description]

        Returns:
            bool: [description]
        """
        return self._alias == alias

    def format_output(self, stdout: str, stderr: str) -> str:
        """Format the stdout and stderr to a single string

        Args:
            stdout (str): Standard output
            stderr (str): Standard error

        Returns:
            str: output text
        """
        output_text = ''

        if stdout and self._use_stdout:
            output_text += stdout

        if stderr and self._use_stderr:
            output_text += stderr
        return output_text


    def execute_command(self, alias: str, timeout: int = 10) -> Tuple[int, str]:
        """Execute a command

        Args:
            alias (str): Command alias which will be transformed to the real command
            timeout (int, optional): Timeout in seconds. Defaults to 10.

        Raises:
            CommandFailedError: Command failed to execute error (non-zero exit code)
            CommandTimeoutError: Command timed out error

        Returns:
            (int, str): Command output in the format of (exit_code, output)
        """
        command = self.transform_command(alias)

        full_command = ['/bin/bash', '-c', f'{command}']
        process = Popen(full_command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode

            output_text = self.format_output(stdout.decode('utf8'), stderr.decode('utf8'))

            if exit_code != 0:
                raise CommandFailedError('command: {self._alias}, exit_code={exit_code},')

            return (exit_code, output_text)
        except TimeoutExpired:
            raise CommandTimeoutError(f'command: {self._alias}')


class CommandAliasWithArgs(CommandAlias):
    """Create a command alias that uses arguments

    Example:
    > CommandAliasWithArgs('show logs (\\w+)', r'journal -u "\\1" -n 100')

    Args:
        CommandAlias ([type]): [description]
    """
    def __init__(self, alias: str, command: str, usage: str = ''):
        super().__init__(alias, command, usage)
        self._template_pattern = re.compile(alias)

    def transform_command(self, alias) -> str:
        return re.sub(self._alias, self._command, alias)

    def is_match(self, alias) -> bool:
        return self._template_pattern.match(alias) is not None

class InvalidCommandError(Exception):
    """Command not found error"""

    details: str = 'Invalid pre-defined command'

    def __init__(self, *args, **kwargs):
        failure_reason: str = (
            f'Invalid command. Command execution is limited to set of pre-defined commands'
        )
        super().__init__(
            failure_reason=failure_reason,
            details=self.details,
            *args,
            **kwargs
        )


class CommandFailedError(Exception):
    """Command failed error"""

    details: str = 'Command failed to execute successfully'

    def __init__(self, *args, **kwargs):
        failure_reason: str = (
            f'A non-zero code was returned by the command.'
        )
        super().__init__(
            failure_reason=failure_reason,
            details=self.details,
            *args,
            **kwargs
        )

class CommandTimeoutError(Exception):
    """Command timeout error"""

    details: str = 'Command timed out before it was finished'

    def __init__(self, *args, **kwargs):
        failure_reason: str = (
            f'Command timeout. ' \
            f'Command are only permitted to run for a short amount of time as defined in the configuration'
        )
        super().__init__(
            failure_reason=failure_reason,
            details=self.details,
            *args,
            **kwargs
        )
