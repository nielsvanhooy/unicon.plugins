"""
Unittests for IOSXR plugin

Uses the mock_device.py script to test IOSXR plugin.

"""

__author__ = "Dave Wapstra <dwapstra@cisco.com>"

import os
import unittest
from textwrap import dedent
from unittest.mock import patch

import unicon
from unicon import Connection
from unicon.core.errors import SubCommandFailure
from unicon.plugins.tests.mock.mock_device_iosxr import MockDeviceTcpWrapperIOSXR
from unicon.eal.dialogs import Dialog
from unicon.mock.mock_device import mockdata_path


unicon.settings.Settings.POST_DISCONNECT_WAIT_SEC = 0
unicon.settings.Settings.GRACEFUL_DISCONNECT_WAIT_SEC = 0.2


class TestIosXrPlugin(unittest.TestCase):
    def test_login_connect_ssh(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state connect_ssh'],
                       os='iosxr',
                       credentials=dict(default=dict(username='admin', password='admin')))
        c.connect()
        self.assertEqual(c.spawn.match.match_output, 'end\r\nRP/0/RP0/CPU0:Router#')

    def test_login_execution(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state enable'],
                       os='iosxr',
                       credentials=dict(default=dict(username='admin', password='admin')))
        c.connect()
        device_output = c.execute('show version')
        with open(os.path.join(mockdata_path, 'iosxr/show_version.txt'), 'r') as outputfile:
            expected_device_output = outputfile.read().strip()
        device_output = device_output.replace('\r', '').strip()
        self.maxDiff = None
        self.assertEqual(device_output, expected_device_output)

    def test_login_ssh_password(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state ssh_password'],
                       os='iosxr',
                       credentials=dict(default=dict(username='admin', password='admin')))
        c.connect()
        self.assertEqual(c.spawn.match.match_output, 'end\r\nRP/0/RP0/CPU0:Router#')

    def test_log_message_before_prompt(self):
        c = Connection(hostname='R1',
                       start=['mock_device_cli --hostname R1 --os iosxr --state enable'],
                       os='iosxr',
                       username='cisco',
                       enable_password='admin',
                       init_config_commands=[],
                       init_exec_commands=[])
        c.connect()

        c.settings.IGNORE_CHATTY_TERM_OUTPUT = False
        c.sendline('process_restart_msg')
        r = c.execute('show telemetry | inc ACTIVE')
        self.assertIn(
            """process_restart_msg
0/RP0/ADMIN0:Jul 7 10:07:42.979 UTC: pm[2890]: %INFRA-Process_Manager-3-PROCESS_RESTART : Process tams (IID: 0) restarted""",
            r.replace('\r', '').replace('\n\n', '\n'))

        c.settings.IGNORE_CHATTY_TERM_OUTPUT = True
        c.sendline('process_restart_msg')
        r = c.execute('show telemetry | inc ACTIVE')
        self.assertEqual(r, 'Sat Jul 7 10:08:02.976 UTC\r\nState: ACTIVE')

    def test_connect_prompts(self):
        for state in [
                'sysadmin_config',
                'sysadmin1',
                'sysadmin2',
                'iosxr_config_ios',
                'xr_vm',
                'xr_vm2'
        ]:
            c = Connection(hostname='Router',
                           start=['mock_device_cli --os iosxr --state %s' % state],
                           os='iosxr',
                           enable_password='cisco',
                           init_exec_commands=[],
                           init_config_commands=[])
            c.connect()

    def test_configure_root_system_username(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state configure_root_system_username'],
                       os='iosxr',
                       username='root',
                       tacacs_password='secretpassword')
        c.connect()

    def test_configure_root_system_username_credential(self):
        c = Connection(
            hostname='Router',
            start=['mock_device_cli --os iosxr --state configure_root_system_username'],
            os='iosxr',
            credentials=dict(default=dict(username='root', password='secretpassword')),
        )
        c.connect()

    def test_connect_learn_hostname(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state enable --hostname xrv-ss-test1'],
                       os='iosxr',
                       init_exec_commands=[],
                       init_config_commands=[],
                       learn_hostname=True)
        c.connect()
        self.assertEqual(c.hostname, 'xrv-ss-test1')

    def test_login_connect_connectReply(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state connect_ssh'],
                       os='iosxr',
                       username='cisco',
                       line_password='admin',
                       enable_password='admin',
                       connect_reply=Dialog([[r'^(.*?)Connected.']]))
        c.connect()
        self.assertEqual(c.spawn.match.match_output, 'end\r\nRP/0/RP0/CPU0:Router#')
        self.assertIn("^(.*?)Connected.", str(c.connection_provider.get_connection_dialog()))
        c.disconnect()

    def test_connect_different_prompt_format(self):
        c = Connection(hostname='KLMER02-SU1', start=['mock_device_cli --os iosxr --state enable4'], os='iosxr')

        c.connect()
        self.assertEqual(c.spawn.match.match_output, 'end\r\nRP/B0/CB0/CPU0:KLMER02-SU1#')
        c.disconnect()

    def test_connect_unresponsive(self):
        con = Connection(
                hostname='R1',
                os='iosxr',
                start=['mock_device_cli --os iosxr --state unresponsive_prompt --hostname R1'],
                credentials=dict(default=dict(username='admin', password='admin')))
        try:
            con.connect()
        finally:
            con.disconnect()


class TestIosXRPluginExecute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Connection(
            hostname='Router',
            start=['mock_device_cli --os iosxr --state enable'],
            os='iosxr',
        )
        cls.c.connect()

    def test_execute_error_pattern(self):
        with self.assertRaises(SubCommandFailure):
            self.c.execute('not a real command')

    def test_execute_error_pattern_negative(self):
        self.c.execute('not a real command partial')


class TestIosXrPluginPrompts(unittest.TestCase):
    """Tests for prompt handling."""
    def setUp(self):
        self._conn = Connection(
            hostname='Router',
            start=['mock_device_cli --os iosxr --state enable'],
            os='iosxr',
        )
        self._conn.connect()

    def test_confirm(self):
        """Check '\n' is sent in response to a [confirm] prompt."""
        self._conn.execute("process restart ifmgr location all")

    def test_confirm_y(self):
        """Check 'y\n' is sent in response to a [y/n] prompt."""
        self._conn.execute("clear logging")

    def test_y_on_repeat_confirm(self):
        self._conn.execute("clear logg")


class TestIosXrConfigPrompts(unittest.TestCase):
    """Tests for config prompt handling."""
    @classmethod
    def setUpClass(self):
        self._conn = Connection(
            hostname='Router',
            start=['mock_device_cli --os iosxr --state enable'],
            os='iosxr',
            mit=True,
            log_buffer=True
        )
        self._conn.connect()

    def test_failed_config(self):
        """Check that we can successfully return to an enable prompt after entering failed config."""
        self._conn.execute("configure terminal", allow_state_change=True)
        self._conn.execute("test failed")
        self._conn.spawn.timeout = 60
        self._conn.enable()

    def test_failed_config_error_message1(self):
        """Check that we can successfully return to an enable prompt after entering failed config."""
        with self.assertRaisesRegex(unicon.core.errors.SubCommandFailure, "% Invalid config"):
            self._conn.configure("test failed")

    def test_failed_config_error_message2(self):
        """Check that we can successfully return to an enable prompt after entering failed config."""
        with self.assertRaisesRegex(unicon.core.errors.SubCommandFailure, "% Invalid config"):
            self._conn.configure("test failed2")

    def test_update_hostname(self):
        self.assertEqual('Router', self._conn.hostname)
        self._conn.configure('hostname R2')
        self.assertEqual('R2', self._conn.hostname)

    def test_config_syslog(self):
        self._conn.execute('config_syslog', allow_state_change=True)
        self._conn.enable()


class TestIosXrPluginAdminService(unittest.TestCase):
    def test_admin(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          enable_password='cisco')

        with conn.admin_console() as console:
            out = console.execute('show platform')
            console.execute('clear configuration inconsistency')
            self.assertIn('IOS XR RUN', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)

    def test_admin_host(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable6'],
                          os='iosxr',
                          enable_password='cisco',
                          mit=True)

        conn.connect()
        with conn.admin_bash_console() as console:
            console.execute('ssh 10.0.2.16', allow_state_change=True)

class TestIosXrPluginBashService(unittest.TestCase):

    def test_bash(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.bash_console() as console:
            console.execute('cd ../common/')
            console.execute('cd ../disk0')
            out = console.execute('pwd')
            self.assertIn('disk0', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)
        conn.disconnect()

    def test_admin_bash(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.admin_bash_console() as console:
            console.execute('cd cisco_support/')
            out = console.execute('ls')
            self.assertIn('event_track', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)
        conn.disconnect()

    def test_bash2(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable2'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.bash_console() as console:
            out = console.execute('pwd')
            self.assertIn('disk0', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)
        conn.disconnect()

    def test_admin_bash2(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable2'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.admin_bash_console() as console:
            out = console.execute('pwd')
            self.assertIn('misc', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)
        conn.disconnect()

    def test_run_prompt_rsp(self):
        conn = Connection(hostname='R1',
                          start=['mock_device_cli --os iosxr --state enable_bash_run_prompt_rsp --hostname R1'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.bash_console():
            pass
        conn.disconnect()

    def test_run_prompt_rp(self):
        conn = Connection(hostname='R2',
                          start=['mock_device_cli --os iosxr --state enable_bash_run_prompt_rp --hostname R2'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.bash_console():
            pass
        conn.disconnect()

    def test_bash5(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable5'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        with conn.bash_console() as console:
            out = console.execute('pwd')
            self.assertIn('disk0', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)
        conn.disconnect()

    def test_admin_host_ios(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state bash_console7'],
                          os='iosxr',
                          mit=True,
                          log_buffer=True)

        conn.connect()
        try:
            conn.execute('run ssh 10.0.2.16', allow_state_change=True)
            self.assertEqual(conn.state_machine.current_state, 'admin_host')
        finally:
            conn.disconnect()


@patch.object(unicon.settings.Settings, 'POST_DISCONNECT_WAIT_SEC', 0)
@patch.object(unicon.settings.Settings, 'GRACEFUL_DISCONNECT_WAIT_SEC', 0.2)
class TestIosXrPluginAdminConfigureService(unittest.TestCase):
    def test_admin_configure(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          enable_password='cisco')
        conn.connect()
        out = conn.admin_configure('show configuration')
        self.assertIn('% No configuration changes found.', out)
        self.assertEqual(conn.state_machine.current_state, 'enable')
        conn.disconnect()

    def test_admin_configure2(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable2'],
                          os='iosxr',
                          enable_password='cisco')
        conn.connect()
        out = conn.admin_configure('show configuration')
        self.assertIn('% No configuration changes found2.', out)
        self.assertEqual(conn.state_machine.current_state, 'enable')
        conn.disconnect()

    def test_admin_configure3(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable2'],
                          os='iosxr',
                          enable_password='cisco')
        conn.connect()
        out = conn.admin_configure('username root\nsecret 123\ngroup cisco-support\nexit')
        self.assertEqual(
            'username root\r\nRP/0/0/CPU0:secret 123\r\nRP/0/0/CPU0:group cisco-support\r\n'
            'RP/0/0/CPU0:exit\r\nRP/0/0/CPU0:commit\r\nRP/0/0/CPU0:', out)
        self.assertEqual(conn.state_machine.current_state, 'enable')
        conn.disconnect()

    def test_ha_admin_configure(self):
        md = MockDeviceTcpWrapperIOSXR(port=0, state='enable1,console_standby')
        md.start()
        conn = Connection(hostname='Router',
                          start=['telnet 127.0.0.1 {}'.format(md.ports[0]), 'telnet 127.0.0.1 {}'.format(md.ports[1])],
                          os='iosxr',
                          username='admin',
                          tacacs_password='admin')
        try:
            conn.connect()
            out = conn.admin_configure('show configuration')
            self.assertIn('% No configuration changes found.', out)
            self.assertEqual(conn.active.state_machine.current_state, 'enable')
            conn.disconnect()
        finally:
            md.stop()

    def test_ha_admin_configure2(self):
        md = MockDeviceTcpWrapperIOSXR(port=0, state='enable2,console_standby')
        md.start()
        conn = Connection(hostname='Router',
                          start=['telnet 127.0.0.1 {}'.format(md.ports[0]), 'telnet 127.0.0.1 {}'.format(md.ports[1])],
                          os='iosxr',
                          username='admin',
                          tacacs_password='admin')
        try:
            conn.connect()
            out = conn.admin_configure('show configuration')
            self.assertIn('% No configuration changes found2.', out)
            self.assertEqual(conn.active.state_machine.current_state, 'enable')
            conn.disconnect()
        finally:
            md.stop()


@patch.object(unicon.settings.Settings, 'POST_DISCONNECT_WAIT_SEC', 0)
@patch.object(unicon.settings.Settings, 'GRACEFUL_DISCONNECT_WAIT_SEC', 0.2)
class TestIosXrPluginAdminExecuteService(unittest.TestCase):
    def test_admin_execute(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          enable_password='cisco')
        conn.connect()
        out = conn.admin_execute('pwd')
        self.assertIn('/misc/disk1', out)
        self.assertEqual(conn.state_machine.current_state, 'enable')
        conn.disconnect()

    def test_admin_configure2(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable2'],
                          os='iosxr',
                          enable_password='cisco')
        conn.connect()
        out = conn.admin_execute('pwd')
        self.assertIn('/misc/disk1:/admin', out)
        self.assertEqual(conn.state_machine.current_state, 'enable')
        conn.disconnect()

    def test_ha_admin_execute(self):
        md = MockDeviceTcpWrapperIOSXR(port=0, state='enable1,console_standby')
        md.start()
        conn = Connection(hostname='Router',
                          start=['telnet 127.0.0.1 {}'.format(md.ports[0]), 'telnet 127.0.0.1 {}'.format(md.ports[1])],
                          os='iosxr',
                          username='admin',
                          tacacs_password='admin')
        conn.connect()
        out = conn.admin_execute('pwd')
        self.assertIn('/misc/disk1', out)
        self.assertEqual(conn.active.state_machine.current_state, 'enable')
        conn.disconnect()
        md.stop()

    def test_ha_admin_execute2(self):
        md = MockDeviceTcpWrapperIOSXR(port=0, state='enable2,console_standby')
        md.start()
        conn = Connection(hostname='Router',
                          start=['telnet 127.0.0.1 {}'.format(md.ports[0]), 'telnet 127.0.0.1 {}'.format(md.ports[1])],
                          os='iosxr',
                          username='admin',
                          tacacs_password='admin')
        conn.connect()
        out = conn.admin_execute('pwd')
        self.assertIn('/misc/disk1:/admin', out)
        self.assertEqual(conn.active.state_machine.current_state, 'enable')
        conn.disconnect()
        md.stop()


class TestIosXrPluginAttachConsoleService(unittest.TestCase):
    def test_attach_console(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          enable_password='cisco')

        with conn.attach_console('0/RP0/CPU0') as console:
            out = console.execute('ls')
            self.assertIn('cmdline', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)

    def test_admin_attach_console(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          enable_password='cisco')

        with conn.admin_attach_console('0/RP0') as console:
            out = console.execute('pwd')
            self.assertIn('/misc/disk1', out)
        ret = conn.spawn.match.match_output
        self.assertIn('exit', ret)
        self.assertIn('Router#', ret)

    def test_admin_attach_console_error(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable1'],
                          os='iosxr',
                          enable_password='cisco')
        with self.assertRaises(SubCommandFailure):
            with conn.admin_attach_console('0/abc', timeout=5) as console:
                console.execute('pwd', timeout=8)


class TestIosxrConfigCommitCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.md = MockDeviceTcpWrapperIOSXR(port=0, state='enable')
        cls.md.start()
        cls.md1 = MockDeviceTcpWrapperIOSXR(port=0, state='login,console_standby')
        cls.md1.start()
        cls.conn = Connection(hostname='Router', start=['telnet 127.0.0.1 {}'.format(cls.md.ports[0])], os='iosxr')
        cls.ha_dev = Connection(hostname='Router',
            start=['telnet 127.0.0.1 {}'.format(cls.md1.ports[0]), 'telnet 127.0.0.1 {}'.format(cls.md1.ports[1])],
            username='admin',
            tacacs_password='admin',
            os='iosxr')
        cls.ha_dev.connect()
        cls.conn.connect()

    @classmethod
    def tearDownClass(cls):
        cls.conn.disconnect()
        cls.ha_dev.disconnect()
        cls.md1.stop()
        cls.md.stop()

    def test_config_commit(self):
        self.conn.configure('no logging console')
        self.ha_dev.configure('no logging console')
        self.assertEqual(self.conn.configure.commit_cmd, 'commit')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit')

    def test_config_commit_replace(self):
        self.conn.configure('no logging console', replace=True)
        self.ha_dev.configure('no logging console', replace=True)
        self.assertEqual(self.conn.configure.commit_cmd, 'commit replace')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit replace')

    def test_config_commit_best_effort(self):
        self.conn.configure('no logging console', best_effort=True)
        self.ha_dev.configure('no logging console', best_effort=True)
        self.assertEqual(self.conn.configure.commit_cmd, 'commit best-effort')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit best-effort')

    def test_config_commit_force(self):
        self.conn.configure('no logging console', force=True)
        self.ha_dev.configure('no logging console', force=True)
        self.assertEqual(self.conn.configure.commit_cmd, 'commit force')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit force')

    def test_bulk_config_commit(self):
        self.conn.configure(['no logging console'] * 2, bulk=True)
        self.ha_dev.configure(['no logging console'] * 2, bulk=True)
        self.assertEqual(self.conn.configure.commit_cmd, 'commit')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit')

    def test_bulk_config_commit_replace(self):
        self.conn.configure(['no logging console'] * 2, replace=True, bulk=True)
        self.ha_dev.configure(['no logging console'] * 2, replace=True, bulk=True)
        self.assertEqual(self.conn.configure.commit_cmd, 'commit replace')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit replace')

    def test_bulk_config_commit_force(self):
        self.conn.configure(['no logging console'] * 2, force=True, bulk=True)
        self.ha_dev.configure(['no logging console'] * 2, force=True, bulk=True)
        self.assertEqual(self.conn.configure.commit_cmd, 'commit force')
        self.assertEqual(self.ha_dev.configure.commit_cmd, 'commit force')

class TestIosxrConfigure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.md = MockDeviceTcpWrapperIOSXR(port=0, state='enable')
        cls.md.start()
        cls.md1 = MockDeviceTcpWrapperIOSXR(port=0, state='login,console_standby')
        cls.md1.start()
        cls.conn = Connection(
            hostname='Router',
            start=['telnet 127.0.0.1 {}'.format(cls.md.ports[0])],
            os='iosxr')
        cls.ha_dev = Connection(
            hostname='Router',
            start=['telnet 127.0.0.1 {}'.format(cls.md1.ports[0]), 'telnet 127.0.0.1 {}'.format(cls.md1.ports[1])],
            username='admin',
            tacacs_password='admin',
            os='iosxr')
        cls.ha_dev.connect()
        cls.conn.connect()

    @classmethod
    def tearDownClass(cls):
        cls.conn.disconnect()
        cls.ha_dev.disconnect()
        cls.md1.stop()
        cls.md.stop()

    def test_configure_error_pattern(self):
        with self.assertRaises(SubCommandFailure):
            self.conn.configure('test failed')
        with self.assertRaises(SubCommandFailure):
            self.ha_dev.configure('test failed')


class TestIosXRPluginPing(unittest.TestCase):
    def test_ping_fail_no_vrf(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state enable'],
                       os='iosxr',
                       username='cisco',
                       tacacs_password='cisco',
                       enable_password='cisco')
        with self.assertRaises(SubCommandFailure):
            c.ping('10.0.0.1')

    def test_ping_success_vrf(self):
        c = Connection(hostname='Router',
                       start=['mock_device_cli --os iosxr --state enable'],
                       os='iosxr',
                       username='cisco',
                       tacacs_password='cisco',
                       enable_password='cisco')
        r = c.ping('10.0.0.2', vrf='management')
        self.assertEqual(r.strip(), "\r\n".join("""ping vrf management 10.0.0.2
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 10.0.0.2, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/1/3 ms
RP/0/RP0/CPU0:""".splitlines()))  # noqa


@patch.object(unicon.settings.Settings, 'POST_DISCONNECT_WAIT_SEC', 0)
@patch.object(unicon.settings.Settings, 'GRACEFUL_DISCONNECT_WAIT_SEC', 0.2)
class TestIosXrPluginConfigureExclusiveService(unittest.TestCase):
    def test_configure_exclusive(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable'],
                          os='iosxr',
                          enable_password='cisco')
        conn.connect()
        out = conn.configure_exclusive('logging console disable')
        self.assertIn('logging console disable', out)
        self.assertEqual(conn.state_machine.current_state, 'enable')
        conn.disconnect()


class TestIosXrPluginReload(unittest.TestCase):

    def test_reload_ncs540(self):
        md = MockDeviceTcpWrapperIOSXR(hostname='R2', port=0, state='ncs540_enable')
        md.start()

        c = Connection(
            hostname='R2',
            start=['telnet 127.0.0.1 {}'.format(md.ports[0])],
            os='iosxr',
            settings=dict(POST_DISCONNECT_WAIT_SEC=0, GRACEFUL_DISCONNECT_WAIT_SEC=0.2),
            credentials=dict(default=dict(username='cisco', password='cisco')),
            init_config_commands=[],
            mit=True,
            log_buffer=True
        )
        try:
            c.connect()
            c.settings.POST_RELOAD_WAIT = 1
            result = c.reload(return_output=True)
            self.assertGreater(len(result.output), 10)
        finally:
            c.disconnect()
            md.stop()

    def test_reload_wish_continue(self):
        conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable7'],
                          os='iosxr',
                          enable_password='cisco',
                          mit=True,
                          settings=dict(POST_RELOAD_WAIT=1))
        try:
            conn.connect()
            conn.reload()
        finally:
            conn.disconnect()


class TestMorePrompt(unittest.TestCase):

    def test_more_prompt(self):
        c = Connection(
            hostname="Router",
            start=["mock_device_cli --os iosxr --state enable"],
            os="iosxr",
            init_exec_commands=[],
            init_config_commands=[],
            settings=dict(POST_DISCONNECT_WAIT_SEC=0, GRACEFUL_DISCONNECT_WAIT_SEC=0.2),
        )
        c.connect()
        try:
            output = c.execute("show command with more")
            self.assertEqual(c.state_machine.current_state, "enable")
            self.assertEqual(output, ' \r\noutput1\r\n \r\noutput2' )
        finally:
            c.disconnect()


class TestXRMonitorCommand(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname='Router',
                          start=['mock_device_cli --os iosxr --state enable'],
                          os='iosxr',
                          enable_password='cisco',
                          mit=True)
        cls.conn.connect()

    @classmethod
    def tearDownClass(cls):
        cls.conn.disconnect()

    def test_monitor_interface_iface(self):
        conn = self.conn
        output = None
        conn.monitor('interface eth0')
        o = conn.monitor('clear')
        self.assertEqual(o, "c\r\nBrief='b', Detail='d', Protocol(IPv4/IPv6)='r'")
        output = conn.monitor.stop()

        self.maxDiff = None

        self.assertEqual(output.replace('\r', '').strip(), dedent("""\
            monitor interface eth0
            R1                   Monitor Time: 00:00:02          SysUptime: 22:48:09

            FourHundredGigE0/0/0/2 is up, line protocol is up
            Encapsulation ARPA

            Traffic Stats:(2 second rates)                                     Delta
              Input  Packets:                      2733                            0

            Quit='q', Freeze='f', Thaw='t', Clear='c', Interface='i',
            Next='n', Prev='p'
            Brief='b', Detail='d', Protocol(IPv4/IPv6)='r'
            c
            Brief='b', Detail='d', Protocol(IPv4/IPv6)='r'
            q"""))

    def test_monitor_interface(self):
        conn = self.conn
        output = None
        conn.monitor('interface')
        output = conn.monitor.stop()
        self.assertEqual(output.replace('\r', '').strip(), dedent("""\
            monitor interface
            R1                   Monitor Time: 00:00:02          SysUptime: 22:48:09

            Quit='q',     Clear='c',    Freeze='f', Thaw='t',
            Next set='n', Prev set='p', Bytes='y',  Packets='k'
            (General='g', IPv4 Uni='4u', IPv4 Multi='4m', IPv6 Uni='6u', IPv6 Multi='6m')
            q"""))

    def test_monitor_not_supported(self):
        conn = self.conn
        with self.assertRaises(SubCommandFailure):
            conn.monitor('something else')

    def test_monitor_tail(self):
        conn = self.conn
        conn.monitor('interface')
        output = conn.monitor.tail(timeout=3)
        self.assertEqual(output.replace('\r', '').strip(), dedent("""\
            monitor interface
            R1                   Monitor Time: 00:00:02          SysUptime: 22:48:09

            Quit='q',     Clear='c',    Freeze='f', Thaw='t',
            Next set='n', Prev set='p', Bytes='y',  Packets='k'
            (General='g', IPv4 Uni='4u', IPv4 Multi='4m', IPv6 Uni='6u', IPv6 Multi='6m')"""))

    def test_monitor_general(self):
        conn = self.conn
        conn.monitor('interface')
        output = conn.monitor('next set')
        expected_output = "n\r\n(General='g', IPv4 Uni='4u', IPv4 Multi='4m', IPv6 Uni='6u', IPv6 Multi='6m')"
        self.assertEqual(output, expected_output)

        output = conn.monitor('general')
        expected_output = "g\r\n(General='g', IPv4 Uni='4u', IPv4 Multi='4m', IPv6 Uni='6u', IPv6 Multi='6m')"
        self.assertEqual(output, expected_output)

        output = conn.monitor('IPv4 Uni')
        expected_output = "4u\r\n(General='g', IPv4 Uni='4u', IPv4 Multi='4m', IPv6 Uni='6u', IPv6 Multi='6m')"
        self.assertEqual(output, expected_output)

        output = conn.monitor('ipv4uni')
        expected_output = "4u\r\n(General='g', IPv4 Uni='4u', IPv4 Multi='4m', IPv6 Uni='6u', IPv6 Multi='6m')"
        self.assertEqual(output, expected_output)



if __name__ == "__main__":
    unittest.main()
