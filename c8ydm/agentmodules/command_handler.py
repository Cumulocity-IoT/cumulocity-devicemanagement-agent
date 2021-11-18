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
import logging
import re
import sys
from typing import List, Optional
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.framework.modulebase import Listener
from c8ydm.core.shell import CommandAlias, CommandAliasWithArgs, InvalidCommandError, CommandFailedError, CommandTimeoutError, TimeoutExpired
class CommandHandler(Listener):

    logger = logging.getLogger(__name__)
    fragment = 'c8y_Command'
    command_message_id = '511'
    _supported_commands = None
    timeout = 60

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        self.agent.publishMessage(executing)

    def _set_success(self):
        success = SmartRESTMessage('s/us', '503', [self.fragment])
        self.agent.publishMessage(success)
    
    def _set_success_with_result(self, result):
        success = SmartRESTMessage('s/us', '503', [self.fragment, result])
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)

    def _get_supported_commands(self) -> List[CommandAlias]:
        """Convert a command alias to its command equalivalent. If not match is found
        then None will be returned.

        Returns:
            Optional[List[CommandAlias]]: Command resolved by the alias
        """
        # Base commands
        commands = [
            CommandAlias('show packages', 'dpkg-query --show'),
            CommandAlias('show processes', 'pgrep -fa \'.+\''),
            CommandAlias('show memory', 'cat /proc/meminfo'),
            CommandAlias('show cpu-usage', 'top -b -n 2'),
            CommandAlias('show disk-usage', 'df -h'),
            CommandAlias('show agent logs', 'cat ~/.cumulocity/agent.log'),
            CommandAlias('remove apt-lists', 'rm -rf /var/lib/apt/lists/*'),
            CommandAliasWithArgs(
                r'show logs (\w+) ?(ERROR|WARN|INFO|DEBUG)?',
                'journalctl -u \\1 -n 100 | grep "\\2"',
                usage='show logs <name> [ERROR|WARN|INFO|DEBUG]'),
        ]

        linux_commands = [
            CommandAlias('show uptime', 'uptime'),
            CommandAlias('show uptime since', 'uptime --since'),
            CommandAlias('show uptime seconds',
                         'awk \'{print $1}\' /proc/uptime'),
            CommandAlias('exec reboot', 'shutdown -r +10'),
        ]
        commands.extend(linux_commands)
        return commands

    def handleOperation(self, message):
        """Callback that is executed for any operation received

            Raises:
            Exception: Error when handling the operation
        """
        if 's/ds' in message.topic and self.command_message_id == message.messageId:
            try:
                self._supported_commands = self._get_supported_commands()
                self.logger.info(f'Supported Commands {self._supported_commands}')
                messages = message.values
                self._set_executing()
                self.logger.info(f'Shell Command Message received: {messages}')

                # Parse command
                raw_cmd = re.sub(r';?\s*\n', '; ', ';'.join(message.values[1:]))
                raw_cmd = re.sub('^"(.*)"$', '\\1', raw_cmd)
                # replace escaped double quote, with literal quote
                raw_cmd = raw_cmd.replace(r'\"', '"')

                # Check for help
                if raw_cmd == 'show help':
                    logging.info(f'Showing shell help')
                   
                    self._set_success_with_result('\n'.join(self._show_help()))
                    return

                resolved_cmd = self._resolve_command(raw_cmd)

                if resolved_cmd:
                    logging.info(f'Using pre-defined command')
                elif self.check_command(raw_cmd):
                    logging.info(f'Using extended command')
                    resolved_cmd = CommandAlias(raw_cmd, raw_cmd)

                if not resolved_cmd:
                    raise InvalidCommandError().add_context(f'command: {raw_cmd}')

                _, output_text = resolved_cmd.execute_command(
                    raw_cmd, timeout=60)
                if sys.getsizeof(output_text) > 16000:
                    self._set_failed(f'Output of command exceeds 16 KB Payload Limit')
                else:
                    self._set_success_with_result(output_text)

            except (InvalidCommandError, CommandFailedError, CommandTimeoutError) as ex:
                logging.error(f'Command error. Exception={ex}')
                self._set_failed(f'{ex}')
            except TimeoutExpired as ex:
                self._set_failed(f'{ex}')
            except Exception as ex:
                logging.error(f'Handling operation error. exception={ex}')
                self._set_failed(f'Unhandled exception. exception={ex}')

    def _resolve_command(self, user_input: str) -> Optional[CommandAlias]:
        """Convert a command alias to its command equalivalent. If not match is found
        then None will be returned.

        Args:
            user_input (str): User input command

        Returns:
            Optional[str]: Command resolved by the alias
        """
        for cmd in self._supported_commands:
            if cmd.is_match(user_input):
                return cmd
        return None
    
    def _show_help(self) -> List[str]:
        """Get the list of usage of the supported commands

        Returns:
            List[str]: List of command usages
        """
        return [cmd.show_usage()
                for cmd in self._supported_commands]

    def _resolve_command(self, user_input: str) -> Optional[CommandAlias]:
        """Convert a command alias to its command equalivalent. If not match is found
        then None will be returned.

        Args:
            user_input (str): User input command

        Returns:
            Optional[str]: Command resolved by the alias
        """
        for cmd in self._supported_commands:
            if cmd.is_match(user_input):
                return cmd
        return None

    @classmethod
    def check_command(cls, cmd: str) -> bool:
        """Check command if it is valid and does not use any forbidden/dangerous commands

        Args:
            cmd (str): command

        Returns:
            bool: True if the command can be run or not
        """
        # allowed_commands = ['cat', 'grep', 'ls', 'uptime']
        forbidden_commands = [
            'alias',
            'nano',
            'reboot',
            'shutdown',
            'vim'
        ]

        forbidden_symbols = [
            '\\e',
            '$',
            '<',
        ]

        forbidden_usage = []
        for item in forbidden_commands:
            match = re.search(fr'\b{item}\s+', cmd)
            match_end = re.search(fr'\b{item}$', cmd)
            if match is not None or match_end is not None:
                logging.warning(
                    f'Detected forbidden command: name={item}, match={match}')
                forbidden_usage.append(item)

        for symbol in forbidden_symbols:
            if symbol in cmd:
                logging.warning(
                    f'Detected forbidden command: name={item}, symbol={symbol}')
                forbidden_usage.append(cmd)

        return len(forbidden_usage) == 0

    def getSupportedOperations(self):
        return [self.fragment]

    def getSupportedTemplates(self):
        return []